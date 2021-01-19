# Fastapi Session

An opinionated fastapi session manager with multiple backends

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

| Backend                                          | Support |
| ------------------------------------------------ | ------- |
| [filesystem](https://github.com/Tinche/aiofiles) | yes     |
| [database](#database)                            | No      |
| [redis](https://github.com/aio-libs/aioredis)    | Yes     |

## Installation

Install the package with [poetry](https://python-poetry.org/):
```sh
$ poetry add fastapi_session
```

## Usage

It's provided with some [examples](./examples) of the library usage using:

* [redis](./examples/redis)
* [filesystem](./examples/filesystem)
* [memory](#memory)
* [database](#database)

## Sources

* [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
