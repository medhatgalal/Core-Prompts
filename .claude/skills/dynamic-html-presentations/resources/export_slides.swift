#!/usr/bin/env swift

import AppKit
import Foundation
import WebKit

enum ExportFailure: Error, LocalizedError {
    case usage(String)
    case invalidInput(String)
    case render(String)

    var errorDescription: String? {
        switch self {
        case .usage(let message), .invalidInput(let message), .render(let message):
            return message
        }
    }
}

struct Options {
    let input: URL
    let output: URL
    let width: Int
    let height: Int
    let selector: String
    let settleMilliseconds: Int
    let timeoutSeconds: TimeInterval
    let force: Bool

    static let help = """
    Usage:
      swift export_slides.swift --input DECK.html --output SLIDES_DIR [options]

    Options:
      --width PIXELS       Output width (default: 1920)
      --height PIXELS      Output height (default: 1080)
      --selector CSS       Slide selector (default: .slide)
      --settle-ms MS       Native paint delay after two animation frames (default: 100)
      --timeout SEC        Overall timeout (default: 120)
      --force              Replace existing slide-*.png files in the output directory
      --help                Show this help
    """

    static func parse(_ arguments: [String]) throws -> Options {
        var values: [String: String] = [:]
        var force = false
        var index = 0

        while index < arguments.count {
            let argument = arguments[index]
            if argument == "--help" || argument == "-h" {
                print(help)
                exit(0)
            }
            if argument == "--force" {
                force = true
                index += 1
                continue
            }
            guard argument.hasPrefix("--") else {
                throw ExportFailure.usage("Unexpected argument: \(argument)\n\n\(help)")
            }
            guard index + 1 < arguments.count else {
                throw ExportFailure.usage("Missing value for \(argument)\n\n\(help)")
            }
            values[argument] = arguments[index + 1]
            index += 2
        }

        guard let inputValue = values["--input"] else {
            throw ExportFailure.usage("--input is required\n\n\(help)")
        }
        guard let outputValue = values["--output"] else {
            throw ExportFailure.usage("--output is required\n\n\(help)")
        }

        let width = try positiveInt(values["--width"] ?? "1920", name: "--width")
        let height = try positiveInt(values["--height"] ?? "1080", name: "--height")
        let settle = try nonnegativeInt(values["--settle-ms"] ?? "100", name: "--settle-ms")
        let timeoutInt = try positiveInt(values["--timeout"] ?? "120", name: "--timeout")
        let selector = values["--selector"] ?? ".slide"
        guard !selector.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw ExportFailure.invalidInput("--selector must not be empty")
        }

        let currentDirectory = URL(fileURLWithPath: FileManager.default.currentDirectoryPath, isDirectory: true)
        let input = URL(fileURLWithPath: inputValue, relativeTo: currentDirectory).standardizedFileURL
        let output = URL(fileURLWithPath: outputValue, relativeTo: currentDirectory).standardizedFileURL

        guard FileManager.default.fileExists(atPath: input.path) else {
            throw ExportFailure.invalidInput("Input HTML does not exist: \(input.path)")
        }
        guard input.pathExtension.lowercased() == "html" || input.pathExtension.lowercased() == "htm" else {
            throw ExportFailure.invalidInput("Input must be an .html or .htm file: \(input.path)")
        }

        return Options(
            input: input,
            output: output,
            width: width,
            height: height,
            selector: selector,
            settleMilliseconds: settle,
            timeoutSeconds: TimeInterval(timeoutInt),
            force: force
        )
    }

    private static func positiveInt(_ value: String, name: String) throws -> Int {
        guard let parsed = Int(value), parsed > 0 else {
            throw ExportFailure.invalidInput("\(name) must be a positive integer")
        }
        return parsed
    }

    private static func nonnegativeInt(_ value: String, name: String) throws -> Int {
        guard let parsed = Int(value), parsed >= 0 else {
            throw ExportFailure.invalidInput("\(name) must be a nonnegative integer")
        }
        return parsed
    }
}

func javascriptString(_ value: String) throws -> String {
    let data = try JSONSerialization.data(withJSONObject: value, options: [.fragmentsAllowed])
    guard let rendered = String(data: data, encoding: .utf8) else {
        throw ExportFailure.invalidInput("Could not encode CSS selector")
    }
    return rendered
}

final class SlideExporter: NSObject, WKNavigationDelegate {
    private let options: Options
    private let webView: WKWebView
    private let encodedSelector: String
    private var timeoutTimer: Timer?
    private var expectedFiles: [URL] = []
    private var stagedFiles: [URL] = []
    private var stagingDirectory: URL?

    init(options: Options) throws {
        self.options = options
        self.encodedSelector = try javascriptString(options.selector)

        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        self.webView = WKWebView(
            frame: CGRect(x: 0, y: 0, width: options.width, height: options.height),
            configuration: configuration
        )
        super.init()
        self.webView.navigationDelegate = self
    }

    func start() throws {
        try prepareOutputDirectory()
        timeoutTimer = Timer.scheduledTimer(withTimeInterval: options.timeoutSeconds, repeats: false) { [weak self] _ in
            self?.finish(.failure(ExportFailure.render("Timed out after \(Int(self?.options.timeoutSeconds ?? 0)) seconds")))
        }
        webView.loadFileURL(options.input, allowingReadAccessTo: options.input.deletingLastPathComponent())
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        let setupScript = """
        (() => {
          const slides = [...document.querySelectorAll(\(encodedSelector))];
          const brokenImages = [...document.images].filter(image =>
            !image.complete || image.naturalWidth === 0 || image.naturalHeight === 0
          );
          if (brokenImages.length > 0) {
            const sources = brokenImages.map(image => image.getAttribute('src') || '(missing src)');
            throw new Error(`Broken image assets: ${sources.join(', ')}`);
          }
          document.body.classList.add('export');
          document.querySelectorAll('.controls, .help, .progress, .notes').forEach(el => {
            el.setAttribute('data-export-hidden', 'true');
          });
          return slides.length;
        })()
        """

        webView.evaluateJavaScript(setupScript) { [weak self] result, error in
            guard let self else { return }
            if let error {
                let details = (error as NSError).userInfo["WKJavaScriptExceptionMessage"] as? String
                    ?? error.localizedDescription
                self.finish(.failure(ExportFailure.render("Could not inspect slides: \(details)")))
                return
            }
            guard let count = (result as? NSNumber)?.intValue, count > 0 else {
                self.finish(.failure(ExportFailure.render("No slides matched selector \(self.options.selector)")))
                return
            }
            let digits = max(2, String(count).count)
            self.expectedFiles = (1...count).map { number in
                self.options.output.appendingPathComponent(String(format: "slide-%0*d.png", digits, number))
            }
            guard let stagingDirectory = self.stagingDirectory else {
                self.finish(.failure(ExportFailure.render("Export staging directory was not initialized")))
                return
            }
            self.stagedFiles = self.expectedFiles.map {
                stagingDirectory.appendingPathComponent($0.lastPathComponent)
            }
            self.renderSlide(index: 0, count: count)
        }
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        finish(.failure(ExportFailure.render("Navigation failed: \(error.localizedDescription)")))
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        finish(.failure(ExportFailure.render("Could not load HTML: \(error.localizedDescription)")))
    }

    private func slidePNGFiles(in directory: URL) throws -> [URL] {
        try FileManager.default.contentsOfDirectory(
            at: directory,
            includingPropertiesForKeys: nil,
            options: [.skipsHiddenFiles]
        ).filter { url in
            url.lastPathComponent.range(of: #"^slide-\d+\.png$"#, options: .regularExpression) != nil
        }.sorted { $0.lastPathComponent < $1.lastPathComponent }
    }

    private func prepareOutputDirectory() throws {
        let manager = FileManager.default
        try manager.createDirectory(at: options.output, withIntermediateDirectories: true)
        let existing = try slidePNGFiles(in: options.output)
        if !existing.isEmpty && !options.force {
            throw ExportFailure.invalidInput(
                "Output contains \(existing.count) slide PNG(s). Use --force to replace slide-*.png files: \(options.output.path)"
            )
        }

        let staging = options.output.appendingPathComponent(
            ".slide-export-\(UUID().uuidString)",
            isDirectory: true
        )
        try manager.createDirectory(at: staging, withIntermediateDirectories: false)
        stagingDirectory = staging
    }

    private func renderSlide(index: Int, count: Int) {
        let activateScript = """
        (() => {
          const slides = [...document.querySelectorAll(\(encodedSelector))];
          if (!slides[\(index)]) throw new Error('Missing slide index \(index)');
          slides.forEach((slide, i) => {
            const active = i === \(index);
            slide.classList.toggle('active', active);
            slide.setAttribute('aria-hidden', String(!active));
          });
          document.body.classList.add('export');
          return true;
        })()
        """

        webView.evaluateJavaScript(activateScript) { [weak self] _, error in
            guard let self else { return }
            if let error {
                self.finish(.failure(ExportFailure.render("Could not activate slide \(index + 1): \(error.localizedDescription)")))
                return
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + .milliseconds(self.options.settleMilliseconds)) {
                self.snapshot(index: index, count: count)
            }
        }
    }

    private func snapshot(index: Int, count: Int) {
        let configuration = WKSnapshotConfiguration()
        configuration.rect = CGRect(x: 0, y: 0, width: options.width, height: options.height)
        configuration.afterScreenUpdates = true

        webView.takeSnapshot(with: configuration) { [weak self] image, error in
            guard let self else { return }
            if let error {
                self.finish(.failure(ExportFailure.render("Snapshot failed for slide \(index + 1): \(error.localizedDescription)")))
                return
            }
            guard let image else {
                self.finish(.failure(ExportFailure.render("Snapshot returned no image for slide \(index + 1)")))
                return
            }

            do {
                let target = self.stagedFiles[index]
                try self.writePNG(image: image, to: target)
                let size = (try FileManager.default.attributesOfItem(atPath: target.path)[.size] as? NSNumber)?.intValue ?? 0
                guard size > 0 else {
                    throw ExportFailure.render("PNG is empty: \(target.path)")
                }
                print("[\(index + 1)/\(count)] \(target.lastPathComponent) (\(size) bytes)")
                if index + 1 < count {
                    self.renderSlide(index: index + 1, count: count)
                } else {
                    self.verifyAndFinish(count: count)
                }
            } catch {
                self.finish(.failure(error))
            }
        }
    }

    private func writePNG(image: NSImage, to target: URL) throws {
        guard let bitmap = NSBitmapImageRep(
            bitmapDataPlanes: nil,
            pixelsWide: options.width,
            pixelsHigh: options.height,
            bitsPerSample: 8,
            samplesPerPixel: 4,
            hasAlpha: true,
            isPlanar: false,
            colorSpaceName: .deviceRGB,
            bytesPerRow: 0,
            bitsPerPixel: 0
        ) else {
            throw ExportFailure.render("Could not create \(options.width)×\(options.height) RGBA bitmap")
        }
        guard let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
            throw ExportFailure.render("Could not create bitmap graphics context")
        }

        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = context
        context.imageInterpolation = .high
        image.draw(
            in: CGRect(x: 0, y: 0, width: options.width, height: options.height),
            from: CGRect(origin: .zero, size: image.size),
            operation: .copy,
            fraction: 1.0
        )
        context.flushGraphics()
        NSGraphicsContext.restoreGraphicsState()

        guard let data = bitmap.representation(using: .png, properties: [:]) else {
            throw ExportFailure.render("Could not encode PNG for \(target.lastPathComponent)")
        }
        try data.write(to: target, options: .atomic)
    }

    private func promoteStagedFiles() throws {
        guard let stagingDirectory else {
            throw ExportFailure.render("Export staging directory was not initialized")
        }

        let manager = FileManager.default
        let existing = try slidePNGFiles(in: options.output)
        let backup = options.output.appendingPathComponent(
            ".slide-backup-\(UUID().uuidString)",
            isDirectory: true
        )
        var promoted: [URL] = []

        do {
            try manager.createDirectory(at: backup, withIntermediateDirectories: false)
            for file in existing {
                try manager.moveItem(at: file, to: backup.appendingPathComponent(file.lastPathComponent))
            }
            for (staged, final) in zip(stagedFiles, expectedFiles) {
                try manager.moveItem(at: staged, to: final)
                promoted.append(final)
            }

            let finalNames = Set(try slidePNGFiles(in: options.output).map(\.lastPathComponent))
            let expectedNames = Set(expectedFiles.map(\.lastPathComponent))
            guard finalNames == expectedNames else {
                throw ExportFailure.render("Promoted PNG set does not match the expected slide set")
            }

            try manager.removeItem(at: stagingDirectory)
            try manager.removeItem(at: backup)
            self.stagingDirectory = nil
        } catch {
            for file in promoted where manager.fileExists(atPath: file.path) {
                try? manager.removeItem(at: file)
            }
            if manager.fileExists(atPath: backup.path),
               let backups = try? manager.contentsOfDirectory(
                   at: backup,
                   includingPropertiesForKeys: nil,
                   options: [.skipsHiddenFiles]
               ) {
                for file in backups {
                    let original = options.output.appendingPathComponent(file.lastPathComponent)
                    if manager.fileExists(atPath: original.path) {
                        try? manager.removeItem(at: original)
                    }
                    try? manager.moveItem(at: file, to: original)
                }
            }
            try? manager.removeItem(at: backup)
            try? manager.removeItem(at: stagingDirectory)
            self.stagingDirectory = nil
            throw error
        }
    }

    private func verifyAndFinish(count: Int) {
        do {
            let missing = stagedFiles.filter { !FileManager.default.fileExists(atPath: $0.path) }
            guard missing.isEmpty else {
                throw ExportFailure.render("Missing \(missing.count) staged PNG(s)")
            }
            try promoteStagedFiles()
            print("Exported and verified \(count) slide(s) at \(options.width)×\(options.height) in \(options.output.path)")
            finish(.success(()))
        } catch {
            finish(.failure(error))
        }
    }

    private func finish(_ result: Result<Void, Error>) {
        timeoutTimer?.invalidate()
        timeoutTimer = nil
        switch result {
        case .success:
            NSApplication.shared.terminate(nil)
        case .failure(let error):
            if let stagingDirectory {
                try? FileManager.default.removeItem(at: stagingDirectory)
                self.stagingDirectory = nil
            }
            fputs("error: \(error.localizedDescription)\n", stderr)
            fflush(stderr)
            exit(1)
        }
    }
}

let application = NSApplication.shared
application.setActivationPolicy(.prohibited)

var retainedExporter: SlideExporter?
do {
    let options = try Options.parse(Array(CommandLine.arguments.dropFirst()))
    retainedExporter = try SlideExporter(options: options)
    try retainedExporter?.start()
    application.run()
} catch {
    fputs("error: \(error.localizedDescription)\n", stderr)
    exit(2)
}
