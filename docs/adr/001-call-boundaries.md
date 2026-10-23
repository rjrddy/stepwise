# Explicit call boundaries rather than monkey-patching

Accepted. Model/tool functions are passed to `Tape.call`. This makes intercepted work visible in code and lets replay avoid all provider/tool invocations. Hidden I/O and streaming are outside the contract. A wrapper around a real provider can be added by the caller; this repo uses only synthetic functions. Redacted replay results cannot reproduce secret-dependent computations. Automatic framework adapters are deferred.
