# Using the SDKs

Start the server. Python import is installed by `make setup`:

```python
from stepwise.sdk import Client
client = Client('http://127.0.0.1:8091', secrets=('synthetic-private-marker',))
run_id, tape = client.record('my synthetic agent')
plan = tape.call('model', 'plan', {'task': 'synthetic'}, lambda p: {'tool': 'lookup'})
result = tape.call('tool', 'lookup', plan, lambda p: {'answer': 'synthetic result'})
# Run the same application logic using the replacement tape:
tape = client.replay(run_id)
plan = tape.call('model', 'plan', {'task': 'synthetic'}, lambda p: None)
result = tape.call('tool', 'lookup', plan, lambda p: None)
tape.finish()
```

Node supports async tool/model functions:

```js
import {Client} from './sdk/node/index.mjs';
const client = new Client('http://127.0.0.1:8091');
const {id, tape} = await client.record('synthetic node agent');
await tape.call('model', 'plan', {task:'synthetic'}, async p => ({tool:'lookup'}));
const replay = await client.replay(id);
await replay.call('model', 'plan', {task:'synthetic'}, () => {throw Error('must not execute')});
replay.finish();
```

Pass token through Client options when required. Register known secrets on both client and server. Models are represented by their input messages and full JSON response inside an explicit call; this is not token-stream tracing or automatic framework interception. One caller per tape; no background spans. Python supports synchronous callables, Node awaits async callables. Avoid unbounded or non-JSON provider objects; normalize them before tracing. JSON numeric values intended for cross-language replay must remain within JavaScript's safe integer range.

Persistence failure propagates after the function may have executed: never blindly retry irreversible tools. Replay errors represent a recorded failure, not the original exception class. `finish()` proves tape exhaustion; omitting it can hide a shortened application run. SDK runs currently remain open for append; there is no retention API or durable pause/edit controller for arbitrary agents.
