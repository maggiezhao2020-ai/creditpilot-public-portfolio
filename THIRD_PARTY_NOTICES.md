# Third-party dependency notices

CreditPilot original project materials: Copyright © 2026 maggiezhao2020-ai. All rights reserved. They are portfolio-only and are not released under an open-source license. This file identifies third-party Python packages resolved for the proposed Streamlit 1.66.0 deployment. Each dependency retains its own license; the entries below do not relicense CreditPilot.

The public source repository contains a `requirements.txt` pin and does **not** vendor these dependency wheels or their source. A host installs them separately. Their installed distributions carry their applicable license files, copyright notices, and, where present, NOTICE files. If dependencies are later bundled into a distributable archive, container, executable, or copied repository, reassess that distribution and carry the applicable complete license and notice texts with it. The hosted app uses these libraries; this inventory does not claim that the server-side Python packages are delivered to browser visitors.

## Production dependency inventory

This is the owner-provided production-only Python 3.12 resolution, excluding pytest and audit tools. It records installed versions for attribution review; `requirements.txt` directly pins only `streamlit==1.66.0`, so another installation may resolve different transitive versions.

| Package | Version | License / installed notice summary |
|---|---:|---|
| altair | 6.3.0 | BSD-3-Clause |
| anyio | 4.15.1 | MIT |
| attrs | 26.1.0 | MIT |
| certifi | 2026.10.18 | MPL-2.0 |
| charset-normalizer | 3.5.2 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| h11 | 0.16.0 | MIT |
| idna | 3.20 | BSD-3-Clause |
| itsdangerous | 2.2.0 | BSD-3-Clause |
| Jinja2 | 3.1.6 | BSD-3-Clause |
| jsonschema | 4.26.0 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| MarkupSafe | 3.0.4 | BSD-3-Clause |
| narwhals | 2.27.1 | MIT |
| numpy | 2.5.4 | BSD-3-Clause; bundled third-party terms below |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pandas | 3.0.6 | BSD-3-Clause |
| pillow | 12.3.0 | MIT-CMU |
| protobuf | 7.36.2 | BSD-3-Clause |
| pyarrow | 26.0.0 | Apache-2.0; NOTICE below |
| pydeck | 0.9.3 | Apache-2.0 |
| python-dateutil | 2.9.0.post0 | Apache-2.0 / BSD-3-Clause |
| python-multipart | 0.0.32 | Apache-2.0 |
| referencing | 0.37.0 | MIT |
| requests | 2.34.2 | Apache-2.0; NOTICE below |
| rpds-py | 2026.9.1 | MIT |
| six | 1.17.0 | MIT |
| starlette | 1.9.0 | BSD-3-Clause |
| streamlit | 1.66.0 | Apache-2.0 |
| typing_extensions | 4.16.0 | PSF-2.0 |
| urllib3 | 2.8.0 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| websockets | 17.2 | BSD-3-Clause |

The Streamlit 1.66.0 release metadata identifies [Apache-2.0](https://pypi.org/project/streamlit/1.66.0/). Its installed distribution reports Apache-2.0 even though the inspected wheel does not list a separate license file. The [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) and any applicable upstream notices govern Streamlit, PyArrow, Requests, PyDeck, python-multipart, and the applicable choice for packaging/python-dateutil. MIT, BSD, MIT-CMU, PSF, and other entries retain their own copyright and license terms.

The inspected NumPy 2.5.4 macOS x86_64 wheel has its own `numpy-2.5.4.dist-info/licenses/LICENSE.txt` and bundled license files. Its bundled notices include OpenBLAS (BSD-3-Clause), LAPACK (BSD-3-Clause-Open-MPI), the GCC runtime (GPL-3.0-or-later WITH GCC-exception-3.1), and libquadmath (LGPL-2.1-or-later), alongside the NumPy and other bundled component notices. These are terms of the installed third-party wheel, not CreditPilot's original code. Preserve the wheel's complete license bundle if redistributing that wheel.

certifi 2026.10.18 identifies its modified Mozilla CA bundle under [MPL-2.0](https://www.mozilla.org/en-US/MPL/2.0/). This repository does not include certifi or modify its files. Running the server with an independently installed certifi package does not distribute its server-side source to visitors. If a future release distributes certifi-covered source or executable files, retain its MPL notice and satisfy the source-availability terms applicable to that distribution.

## Upstream NOTICE files reviewed

The following blocks reproduce the installed PyArrow and Requests NOTICE files verbatim. They concern those projects and their included components; they are not CreditPilot copyright statements.

### Apache Arrow / PyArrow 26.0.0

```text
Apache Arrow
Copyright 2016-2026 The Apache Software Foundation

This product includes software developed at
The Apache Software Foundation (http://www.apache.org/).

This product includes software from the SFrame project (BSD, 3-clause).
* Copyright (C) 2015 Dato, Inc.
* Copyright (c) 2009 Carnegie Mellon University.

This product includes software from the Feather project (Apache 2.0)
https://github.com/wesm/feather

This product includes software from the DyND project (BSD 2-clause)
https://github.com/libdynd

This product includes software from the LLVM project
 * distributed under the University of Illinois Open Source

This product includes software from the mman-win32 project
 * Copyright https://code.google.com/p/mman-win32/
 * Licensed under the MIT License;

This product includes software from the LevelDB project
 * Copyright (c) 2011 The LevelDB Authors. All rights reserved.
 * Use of this source code is governed by a BSD-style license that can be
 * Moved from Kudu http://github.com/cloudera/kudu

This product includes software from the CMake project
 * Copyright 2001-2009 Kitware, Inc.
 * Copyright 2012-2014 Continuum Analytics, Inc.
 * All rights reserved.

This product includes software from https://github.com/matthew-brett/multibuild (BSD 2-clause)
 * Copyright (c) 2013-2016, Matt Terry and Matthew Brett; all rights reserved.

This product includes software from the Ibis project (Apache 2.0)
 * Copyright (c) 2015 Cloudera, Inc.
 * https://github.com/cloudera/ibis

This product includes software from Dremio (Apache 2.0)
  * Copyright (C) 2017-2018 Dremio Corporation
  * https://github.com/dremio/dremio-oss

This product includes software from Google Guava (Apache 2.0)
  * Copyright (C) 2007 The Guava Authors
  * https://github.com/google/guava

This product include software from CMake (BSD 3-Clause)
  * CMake - Cross Platform Makefile Generator
  * Copyright 2000-2019 Kitware, Inc. and Contributors

The web site includes files generated by Jekyll.

--------------------------------------------------------------------------------

This product includes code from Apache Kudu, which includes the following in
its NOTICE file:

  Apache Kudu
  Copyright 2016 The Apache Software Foundation

  This product includes software developed at
  The Apache Software Foundation (http://www.apache.org/).

  Portions of this software were developed at
  Cloudera, Inc (http://www.cloudera.com/).

--------------------------------------------------------------------------------

This product includes code from Apache ORC, which includes the following in
its NOTICE file:

  Apache ORC
  Copyright 2013-2019 The Apache Software Foundation

  This product includes software developed by The Apache Software
  Foundation (http://www.apache.org/).

  This product includes software developed by Hewlett-Packard:
  (c) Copyright [2014-2015] Hewlett-Packard Development Company, L.P
```

### Requests 2.34.2

```text
Requests
Copyright 2019 Kenneth Reitz
```

