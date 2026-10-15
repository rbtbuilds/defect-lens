# Security and limits

This v1 is a local, single-operator demonstration without authentication. Bind only to 127.0.0.1 and use the exact web origin http://127.0.0.1:5111. Do not expose it to a network or use it for safety-critical inspection. A local process with access to this user's filesystem is inside the trust boundary; this application does not provide tenant isolation.

Image/body/dimension caps, a bounded queue, deadlines, worker RSS monitoring, contained artifact paths, immutable model checksums and transactional idempotency reduce accidental resource exhaustion and ambiguity. The decoder validates dimensions and decodes pixels; it does not certify every container checksum or terminator. Recoverable missing PNG metadata can be accepted and normalized. These controls are not a production security certification. Model artifacts are JSON and NumPy with allow_pickle=False; checkpoint loading uses weights_only=True after checksum verification. Do not load untrusted manually edited artifacts.

Keep originals, database, local aliases/notes, logs and ownership records private. An operator alias is not authenticated identity. Origin checking is useful for a local browser flow and does not replace authentication or a server authorization model.

If you find a vulnerability, preserve a minimal local reproduction and share it privately with the repository owner through a contact you already know. No dedicated reporting address has been verified. Do not publish secrets, private images or exploit details in a public issue.
