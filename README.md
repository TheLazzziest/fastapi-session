# Fastapi Session

An opinionated fastapi session manager with multiple backends

**Notice**:

*Please, keep in mind that this library is still under heavy development. So changes of **any type** may happend. The [main](https://github.com/TheLazzziest/fastapi_session) branch is almost always stable. However, it is better to stick with release tags in order to mitigate error catching. Covering the project with tests takes one of the first places during development. However, it is not much time to test more thoroughly, so, please, be patient if something doesn't work properly or you faced with the outdated documentation or examples. BTW, new issues and pull requests are always welcome :)*

## Requirements

* [Python](https://docs.python.org/3.7/tutorial/) >= 3.7
* [pickle](https://docs.python.org/3.7/library/pickle.html)
* [aioredis](https://github.com/aio-libs/aioredis)
* [portalocker](https://github.com/WoLpH/portalocker)

## Features

* Support multiple type of backends out-of-the-box
* Support integration with a custom backend
* Tightly intergrated with FastAPI
* Focused on secured data storing

## Supported backends

| Backend                                                          | Support |
| ---------------------------------------------------------------- | ------- |
| [filesystem + portalocker](https://github.com/WoLpH/portalocker) | yes     |
| [database](#database)                                            | No      |
| [redis](https://github.com/aio-libs/aioredis)                    | Yes     |

## Installation

Install the package with [poetry](https://python-poetry.org/):
```sh
$ poetry add git+ssh://git@github.com:TheLazzziest/fastapi_session.git@0.6.5
```

## Usage

It's provided with some [examples](./examples) of the library usage using:

* [redis](./examples/redis)
* [filesystem](./examples/filesystem)
* [database](#database)

## Sources

* [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
