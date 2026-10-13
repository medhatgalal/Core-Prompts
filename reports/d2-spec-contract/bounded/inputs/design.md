# Supplied redemption design

POST /redeem accepts token and principal_id. Read the token's expires_at and reject if expired. Query team_membership for the current principal; if membership exists, return already_redeemed. Otherwise create a team_membership and return success.

Membership has a unique constraint on (team_id, principal_id). No other persistent redemption record or transaction boundary is described. This design excerpt has no approval record.
