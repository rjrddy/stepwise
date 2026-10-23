.venv/bin/ruff check src tests scripts
E501 Line too long (174 > 100)
  --> scripts/render_readme.py:18:101
   |
16 | …
17 | …
18 | …daries so you can inspect, replay and fork a synthetic workflow without overwriting its original trace.
   |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | …
20 | …
   |

E501 Line too long (193 > 100)
  --> scripts/render_readme.py:22:101
   |
20 | …
21 | …
22 | …; {counts[-1]} tests pass ([raw run](docs/results/gates-and-bench.txt), [hash proofs](docs/results/replay.json)).
   |                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
23 | …summary["memory"]:.3f} µs; synchronous HTTP/Postgres {summary["http_postgres"] / 1000:.3f} ms ([samples](docs/results/bench.json)).
24 | ….3f} ms vs SQL {sql:.3f} ms median; real UI recording {float(b["ffprobe"]["format"]["duration"]):.2f} s ([browser proof](docs/results…
   |

E501 Line too long (211 > 100)
  --> scripts/render_readme.py:23:101
   |
22 | …[-1]} tests pass ([raw run](docs/results/gates-and-bench.txt), [hash proofs](docs/results/replay.json)).
23 | …memory"]:.3f} µs; synchronous HTTP/Postgres {summary["http_postgres"] / 1000:.3f} ms ([samples](docs/results/bench.json)).
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
24 | …s SQL {sql:.3f} ms median; real UI recording {float(b["ffprobe"]["format"]["duration"]):.2f} s ([browser proof](docs/results/browser/…
   |

E501 Line too long (275 > 100)
  --> scripts/render_readme.py:24:101
   |
22 | …tests pass ([raw run](docs/results/gates-and-bench.txt), [hash proofs](docs/results/replay.json)).
23 | …"]:.3f} µs; synchronous HTTP/Postgres {summary["http_postgres"] / 1000:.3f} ms ([samples](docs/results/bench.json)).
24 | …{sql:.3f} ms median; real UI recording {float(b["ffprobe"]["format"]["duration"]):.2f} s ([browser proof](docs/results/browser/review.json)); human diagnosis time **not measured**.
   |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
25 | …
26 | …
   |

E501 Line too long (286 > 100)
  --> scripts/render_readme.py:43:101
   |
41 | …
42 | …
43 | … account or dataset download. `make demo` owns a temporary database; set DATABASE_URL only for an explicitly owned persistent database. Existing traces on a supplied database are not cleared.
   |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
44 | …
45 | …
   |

E501 Line too long (250 > 100)
  --> scripts/render_readme.py:51:101
   |
49 | …
50 | …
51 | …Connection settings. See [demo and recording steps](docs/DEMO.md), [SDK examples](docs/SDK.md), and the [actual recording](docs/results/browser/demo.webm).
   |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
52 | …
53 | …
   |

E501 Line too long (489 > 100)
  --> scripts/render_readme.py:55:101
   |
53 | …
54 | …
55 | … implemented for an explicit synthetic workflow. G…measured or implemented. Nothing is deployed.
   |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^…^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
56 | …
57 | … equality means canonical **redacted call payloads** (including failures), excluding timing and run metadata. A configured secret cannot be reconstructed. The demo replay reruns its continuation logic; an uploaded SDK trace must be replayed inside its calling application to verify that application's behavior. The API cannot execute arbitrary uploaded code.
   |

E501 Line too long (453 > 100)
  --> scripts/render_readme.py:57:101
   |
55 | … implemented for an explicit synthetic workflow. Generic Python/Node application traces support call capture, inspection, diff and application-driven replay; arbitrary application pause/edit/resume is unfinished. Human diagnosis-time improvement, actual model-provider integrations, streaming, multitenant authorization and hosted operation are not measured or im…
56 | …
57 | … equality means canonical **redacted call payloads…e API cannot execute arbitrary uploaded code.
   |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^…^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
58 | …
59 | …effects and trace commits are not atomic. Synchronous persistence fails closed and has visible cost; neither pooling nor asynchronous buffering conceals that cost. One worker per SDK tape. Per-run/body limits do not bound database growth. See [design](docs/DESIGN.md) and [ADRs](docs/adr/).
   |

E501 Line too long (385 > 100)
  --> scripts/render_readme.py:59:101
   |
57 | … equality means canonical **redacted call payloads** (including failures), excluding timing and run metadata. A configured secret cannot be reconstructed. The demo replay reruns its continuation logic; an uploaded SDK trace must be replayed inside its calling application to verify that applicat…
58 | …
59 | …effects and trace commits are not atomic. Synchron…esign](docs/DESIGN.md) and [ADRs](docs/adr/).
   |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^…^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
60 | …
61 | …dicate, not a person discovering a bug or navigating this UI. Node memory samples are separate; Node HTTP overhead is not separately measured. Results are local, small-workload observations, not production forecasts.
   |

E501 Line too long (311 > 100)
  --> scripts/render_readme.py:61:101
   |
59 | …effects and trace commits are not atomic. Synchronous persistence fails closed and has visible cost; neither pooling nor asynchronous buffering conceals that cost. One worker per SDK tape. Per-run/body limits do not bound…
60 | …
61 | …dicate, not a person discovering a bug or navigating this UI. Node memory samples are separate; Node HTTP overhead is not separately measured. Results are local, small-workload observations, not production forecasts.
   |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
62 | …
63 | …utdated bundled pip rejected by dependency scan](docs/results/caught-outdated-pip-audit.txt), repaired [clean scan](docs/results/python-audit.txt); tests cover stale revisions, conflicting writes, actual process exit befo…
   |

E501 Line too long (530 > 100)
  --> scripts/render_readme.py:63:101
   |
61 | …dicate, not a person discovering a bug or navigating this UI. Node memory samples are separate; Node HTTP overhead is not separately measured. Results are local, small-workload observations, not production forecasts.
62 | …
63 | …utdated bundled pip rejected by dependency scan](d… and original design](docs/UI_REFERENCES.md).
   |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^…^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
64 | …
65 | …cs/migration/stepwise.md) · [CI](https://github.com/rjrddy/stepwise/actions)
   |

E501 Line too long (171 > 100)
  --> scripts/render_readme.py:65:101
   |
63 | …s/caught-failure.json), [outdated bundled pip rejected by dependency scan](docs/results/caught-outdated-pip-audit.txt), repaired [cle…
64 | …
65 | … [Migration provenance](docs/migration/stepwise.md) · [CI](https://github.com/rjrddy/stepwise/actions)
   |                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
66 | …
67 | …
   |

E501 Line too long (353 > 100)
  --> scripts/render_readme.py:69:101
   |
67 | …
68 | …
69 | …ough an explicit adapter; streaming/async spans; pooled batched ingest with a documented loss budget; user identities, retention and trace pagination; a counterbalanced human diagnosis study. Integrate with Lean only after it independently passes its checks.
   |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
70 | …
71 | …
   |

Found 13 errors.
make: *** [lint] Error 1
