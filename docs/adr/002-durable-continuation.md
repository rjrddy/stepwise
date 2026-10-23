# Persist a JSON continuation and fork edits

Accepted. Run-row locks plus optimistic revisions serialize state changes. Breakpoints stop before a tool, and edits fork a prefix in a single transaction. Original traces have no update endpoint. Generic application stacks are not serializable here: arbitrary SDK pause/edit/resume requires a cooperative continuation adapter and is an explicit partial gap. External tool effects are not transactionally coupled to Postgres.
