# Changelog

## [1.5.0](https://github.com/equinor/dm-cli/compare/v1.4.3...v1.5.0) (2024-01-19)


### Features

* option to validate on 'entity' command + separate validate command ([70a0238](https://github.com/equinor/dm-cli/commit/70a0238a3e49d42114cc30af72257b29dbadae13))
* option to validate plugin blueprints ([ad28dfc](https://github.com/equinor/dm-cli/commit/ad28dfc85005213e2a64f5fc4e56e043a0b8604e))


### Bug Fixes

* _meta_ might not exist in every package.json ([57a5338](https://github.com/equinor/dm-cli/commit/57a5338574a1971fa6dd81a9eff468e6ab5f5226))

## [1.4.3](https://github.com/equinor/dm-cli/compare/v1.4.2...v1.4.3) (2023-12-18)


### Bug Fixes

* relative storage references ([bf9cc4f](https://github.com/equinor/dm-cli/commit/bf9cc4f2af83784110d60bb7adf111c828bc2d31))
* resolve global files on disk ([d5809c9](https://github.com/equinor/dm-cli/commit/d5809c9383f1e2dd3571cd1873a7c6ccb74e1e63))

## [1.4.2](https://github.com/equinor/dm-cli/compare/v1.4.1...v1.4.2) (2023-12-16)


### Bug Fixes

* ignore tilde symbol ([47592e7](https://github.com/equinor/dm-cli/commit/47592e79475fa0a06d14a33aaef0a951cba0e427))

## [1.4.1](https://github.com/equinor/dm-cli/compare/v1.4.0...v1.4.1) (2023-12-08)


### Bug Fixes

* resolve storage references on disk ([0ce0722](https://github.com/equinor/dm-cli/commit/0ce0722a6dcbf9906f6db2103acc1f05ea60e69c))

## [1.4.0](https://github.com/equinor/dm-cli/compare/v1.3.0...v1.4.0) (2023-11-24)


### Features

* add enum support ([3a5edeb](https://github.com/equinor/dm-cli/commit/3a5edeb650a84b1fa6837d69e7b726c0ca9e87c6))
* resolve enum type ([0d6fe2a](https://github.com/equinor/dm-cli/commit/0d6fe2a040c8ccee6410f3253b0a4fb74e1c9c46))

## [1.3.0](https://github.com/equinor/dm-cli/compare/v1.2.0...v1.3.0) (2023-11-21)


### Features

* retry requests on network errors ([098845c](https://github.com/equinor/dm-cli/commit/098845c6da5ca107d44d8d20b37b6e6a2d60ec96))

## [1.2.0](https://github.com/equinor/dm-cli/compare/v1.1.2...v1.2.0) (2023-10-06)


### Features

* add support for global data source storage ([89a810b](https://github.com/equinor/dm-cli/commit/89a810bf8effcacc49c11a520b5c7cada4182f2b))
* resolve local id ([b8ce10a](https://github.com/equinor/dm-cli/commit/b8ce10a3d3da752c29f03519b12c1a9218966f3d))


### Code Refactoring

* from PR feedback ([b10c028](https://github.com/equinor/dm-cli/commit/b10c02843f21fbf014d67aab00ad74d7b62666ae))

## [1.1.2](https://github.com/equinor/dm-cli/compare/v1.1.1...v1.1.2) (2023-09-15)


### Bug Fixes

* support any attribute type ([d1629e8](https://github.com/equinor/dm-cli/commit/d1629e8d08d3a7de8bd9cd92659067510cda4b60))


### Miscellaneous Chores

* fix api generator scope ([be2efef](https://github.com/equinor/dm-cli/commit/be2efefff7066575bf162e8b07a6f8816822f415))


### Code Refactoring

* import simple for reset command ([20edaaf](https://github.com/equinor/dm-cli/commit/20edaaf76424ff6070c5ba4562f9ddd9daa24162))

## [1.1.1](https://github.com/equinor/dm-cli/compare/v1.1.0...v1.1.1) (2023-09-14)


### Bug Fixes

* temporary fix for OpenApi type conversion error ([7e322b9](https://github.com/equinor/dm-cli/commit/7e322b98e4cd08a7670b534f147db216f7a69d37))

## [1.1.0](https://github.com/equinor/dm-cli/compare/v1.0.14...v1.1.0) (2023-08-31)


### Features

* validate entities after init command ([8a0e5da](https://github.com/equinor/dm-cli/commit/8a0e5dad39fce7ec5f245d07e1507ea2976faf95))
* validate entities after reset command ([d128ece](https://github.com/equinor/dm-cli/commit/d128ece3b23ba0a85afc21d06001930b02e349fa))


### Bug Fixes

* make path concatenation in utils.py os independent ([772c477](https://github.com/equinor/dm-cli/commit/772c477213ab54dbb8b848d59a73b6ca34bb99bb))
* package content should be reference type storage ([ecce8e1](https://github.com/equinor/dm-cli/commit/ecce8e10699f488cbd0bcea2f58ac50d53d19ac4))
* replace references in meta for subpackage on reset command ([48d5c6b](https://github.com/equinor/dm-cli/commit/48d5c6bc896309e2dc5ea37cc515a4baa9ae9621))
* udpate get_root_packages_in_data_sources() to only interpret folders as root package (not single files) ([fca5fb3](https://github.com/equinor/dm-cli/commit/fca5fb353657248e2afb95515ba8a1df8aa25ef2))


### Documentation

* update documentation for cli commands ([716d8a3](https://github.com/equinor/dm-cli/commit/716d8a382827dee3b243af6eacb7c1b25158a67d))


### Styles

* run pretty-format-json ([a2642cc](https://github.com/equinor/dm-cli/commit/a2642ccbfec8b461bf75110f8ddf5f024b62a3e3))


### Miscellaneous Chores

* cleanup ([772c477](https://github.com/equinor/dm-cli/commit/772c477213ab54dbb8b848d59a73b6ca34bb99bb))
* fix test ([772c477](https://github.com/equinor/dm-cli/commit/772c477213ab54dbb8b848d59a73b6ca34bb99bb))
* generate new dmss api ([2778f2c](https://github.com/equinor/dm-cli/commit/2778f2c162083372e7a0ceb85593ea081c5b3d43))
* generate new dmss api (v1.3.0) ([#130](https://github.com/equinor/dm-cli/issues/130)) ([b4a13a1](https://github.com/equinor/dm-cli/commit/b4a13a1a628fdde3a0c80137e33594ec3609220b))
* **pre-commit:** add and update hooks ([59c6b9c](https://github.com/equinor/dm-cli/commit/59c6b9c3280bd818472b33fcb7a643fea0fad773)), closes [#507](https://github.com/equinor/dm-cli/issues/507)
* update codeowners ([01c5250](https://github.com/equinor/dm-cli/commit/01c52507fab75927bead51601ba47b52934c3084))
* update dependencies ([3a156c1](https://github.com/equinor/dm-cli/commit/3a156c14241fd301651f20a91f5124ae5ea76a28))
* update python to 3.11 ([04faf51](https://github.com/equinor/dm-cli/commit/04faf51c211c6c646bd6e7d7157c6550029363fc))
* upgrade dependencies ([1a1363f](https://github.com/equinor/dm-cli/commit/1a1363f74a30820223edc552252aa3c5e3839175))


### Code Refactoring

* update dmss api ([2dd8970](https://github.com/equinor/dm-cli/commit/2dd89707c7af816f59d3219c10a5fa40a694d4cd))


### Continuous Integration

* add release please ([0e4592e](https://github.com/equinor/dm-cli/commit/0e4592e4e267b1e67e10786150b041a6cfb9e9d9))
* avoid running no-commit-to-branch on PR merge ([8bfd4cb](https://github.com/equinor/dm-cli/commit/8bfd4cb135d939dcbdc2ecd3fd651a54bbb00792))
