# Fastapi Session

An opinionated fastapi session manager with multiple backends

**Notice**:

_Please, keep in mind that this library is still under heavy development. So changes of **any type** may happend. The [main](https://github.com/TheLazzziest/fastapi_session) branch is almost stable most of the time. However, it is better to stick with release tags in order to mitigate error catching. Covering the project with tests takes one of the first places during development. However, it is not much time to test more thoroughly, so, please, be patient if something doesn't work properly or you faced with the outdated documentation or examples. BTW, new issues and pull requests are always welcome :)_

## Requirements

* [Python](https://docs.python.org/3.7/tutorial/) >= 3.7
* [pickle](https://docs.python.org/3.7/library/pickle.html)
* [aioredis](https://github.com/aio-libs/aioredis) >= 1.3.1
* [portalocker](https://github.com/WoLpH/portalocker) >= 2.0.0
* [cryptography](https://cryptography.io/en/3.4.6/index.html) >= 3.4.6

## Features

* Support multiple type of backends out-of-the-box
* Support integration with a custom backend
* Tightly intergrated with FastAPI
* Focused on a token security and privacy

## Supported backends

| Backend                                                          | Support |
| ---------------------------------------------------------------- | ------- |
| [filesystem + portalocker](https://github.com/WoLpH/portalocker) | yes     |
| [database](#database)                                            | No      |
| [redis](https://github.com/aio-libs/aioredis)                    | Yes     |

## Installation

Install the package with [poetry](https://python-poetry.org/):

```sh
$ poetry add git+ssh://git@github.com:TheLazzziest/fastapi_session.git#0.6.6
```

## Startup

### Create a fernet token

### Connect the session to an app

```python

```

## Examples

There are some [examples](./examples) of the library usage with the following backends:

* [redis](./examples/redis)
* [filesystem](./examples/filesystem)
* [database](#database)

## Sources

* [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
* [Cryptography](https://cryptobook.nakov.com/encryption-symmetric-and-asymmetric)
* [Fernet](https://github.com/fernet/spec/blob/master/Spec.md)
