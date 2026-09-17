# API / Contracts — PM Query Library Architecture Exercise

Source: [PM Query Library Architecture Overview](https://docs.appian-stratus.io/process-mining/new-arch/#api--contracts)

| Direction | Interface | Purpose | Producer | Consumer | Contract state | Evidence | Owner/action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Provides | `POST /analytics/business-processes/{appianId}/query-metrics` | Aggregation queries | LCP REST layer | ProcessHQ UI | exists_and_works (as documented) | Exemplar API / Contracts | LCP API owner maintains endpoint contract |
| Provides | `POST /analytics/business-processes/{appianId}/explore-attributes` | Attribute exploration | LCP REST layer | ProcessHQ UI | exists_and_works (as documented) | Exemplar API / Contracts | LCP API owner maintains endpoint contract |
| Provides | `POST /analytics/business-processes/{appianId}/discover-model-statistics` | Process model discovery | LCP REST layer | ProcessHQ UI | exists_and_works (as documented) | Exemplar API / Contracts | LCP API owner maintains endpoint contract |
| Provides | `POST /analytics/business-processes/{appianId}/discover-cases` | Case listing | LCP REST layer | ProcessHQ UI | exists_and_works (as documented) | Exemplar API / Contracts | LCP API owner maintains endpoint contract |
| Provides | `POST /analytics/business-processes/{appianId}/discover-case-events` | Case event details | LCP REST layer | ProcessHQ UI | exists_and_works (as documented) | Exemplar API / Contracts | LCP API owner maintains endpoint contract |
| Requires | `aggregate(logUuid, requestJson, mode)` | KPI, metric, and grouping queries | pm-query-lib | LCP client | exists_and_works (as documented) | Exemplar API / Contracts | pm-query-lib owner preserves input/output shape |
| Requires | `discoverModel(logUuid, requestJson)` | Model statistics | pm-query-lib | LCP client | exists_and_works (as documented) | Exemplar API / Contracts | pm-query-lib owner preserves input/output shape |
| Requires | `discoverCases(logUuid, requestJson)` | Filtered case listing | pm-query-lib | LCP client | exists_and_works (as documented) | Exemplar API / Contracts | pm-query-lib owner preserves input/output shape |
| Requires | `discoverCaseEvents(logUuid, requestJson)` | Events for a case | pm-query-lib | LCP client | exists_and_works (as documented) | Exemplar API / Contracts | pm-query-lib owner preserves input/output shape |
| Requires | `exploreAttributes(logUuid, requestJson)` | Attribute distributions | pm-query-lib | LCP client | exists_and_works (as documented) | Exemplar API / Contracts | pm-query-lib owner preserves input/output shape |
| Requires | `preprocess(logUuid, columnMappings, tables)` | Create analytical tables | pm-query-lib | ADS through Data Client | exists_and_works (as documented) | Exemplar API / Contracts; Preprocessing | pm-query-lib + ADS owners preserve table prefixing |
| Requires | ADS Data Client gRPC query / CTAS path | Execute query and preprocessing work | ADS Data Client | ADS | exists_and_works (as documented) | Exemplar Data Flow; ADS Data Client | Data Client / ADS owners preserve gRPC and CTAS contracts |

The state is deliberately qualified as “as documented”: this exercise proves
artifact completeness and faithful extraction from the exemplar, not a live
production integration test.
