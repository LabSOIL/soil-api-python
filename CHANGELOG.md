# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2024-07-18

### Added

- Add basic transect functionality - although still a bit buggy.
- Migrate the functionality from the [InstrumentProcessing.ipynb](https://github.com/LabSOIL/lab-codes/blob/cfd502f2d46596870033fabb570d79bcf8449fa5/InstrumentProcessing.ipynb) notebook in the [lab-codes](https://github.com/LabSOIL/lab-codes) repository functionality into the `Instrument Processing` tab.


## [1.1.3] - 2024-06-28

### Added

- Fulltext query on `str` fields in the database when using `q` filter.
- Delete many functionality for all tables.
- Get elevation on `plot` table if elevation (`coord_z`) is set to 0.
- Bulk update on `plot` table.
- GNSS table.
- Image to soil type.


### Changed

- Set create many on `plot` table with list of records instead of CSV.
- Enum field for `plot` table on Gradient. DB migration reflects addition of
Enum field.
- Exception handling for validation errors on bulk import.
- Cascade delete on Plots to plot samples.

### Fixed

- AreaRead issue when updating Area objects.
- Single point not rendering polygon in geom output.


## [1.1.2] - 2024-06-10

### Added

- This changelog file.
- Base64 images can now be stored in the database. Large images retrieved
by the API are resized to a defined maximum size in the config file.
- Date updated column in all tables.

[unreleased]: https://github.com/LabSOIL/soil-api/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/LabSOIL/soil-api/compare/0.1.2...1.2.0
[1.1.2]: https://github.com/LabSOIL/soil-api/compare/0.0.1...0.1.2
[1.1.3]: https://github.com/LabSOIL/soil-api/compare/0.0.2...0.1.3
