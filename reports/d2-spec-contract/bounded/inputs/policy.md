# Invitation behavior requested

A team owner can invite a person with a token. A token is valid only when current_time < expires_at. At or after expires_at, redemption must be rejected without changing membership.

Each token may produce at most one successful redemption ever. Removing a membership or changing the redeeming principal after a successful redemption must not make that token reusable. Two simultaneous valid attempts for the same token must not both succeed. Invalid tokens do not change membership. Legitimate unused, unexpired tokens must still work.

The present authorization is to prepare a specification using the supplied design. Implementation and acceptance of unresolved technical choices are not authorized. No final accepted draft revision has been recorded.
