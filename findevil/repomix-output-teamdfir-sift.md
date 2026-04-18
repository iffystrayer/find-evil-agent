This file is a merged representation of the entire codebase, combined into a single document by Repomix.
The content has been processed where security check has been disabled.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Security check has been disabled - content may contain sensitive information
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
.github/
  stale.yml
LICENSE
README.md
```

# Files

## File: .github/stale.yml
````yaml
# Number of days of inactivity before an issue becomes stale
daysUntilStale: 60
# Number of days of inactivity before a stale issue is closed
daysUntilClose: 7
# Issues with these labels will never be considered stale
exemptLabels:
  - priority/high
  - kind/security
  - status/accepted
# Label to use when marking an issue as stale
staleLabel: wontfix
# Comment to post when marking an issue as stale. Set to `false` to disable
markComment: >
  This issue has been automatically marked as stale because it has not had
  recent activity. It will be closed if no further activity occurs. Thank you
  for your contributions.
# Comment to post when closing a stale issue. Set to `false` to disable
closeComment: false
````

## File: LICENSE
````
MIT License

Copyright (c) 2018 Harbingers LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
````

## File: README.md
````markdown
<img align="right" src="https://images.contentstack.io/v3/assets/blt36c2e63521272fdc/blt3e371eacc79a3ca4/60a5393fe2db156d00f0b8ab/400x460_DFIR_SIFT.jpg" />

# SIFT

This is a metadata repository that is primarily used for discussiosn and issue tracking. 

- [cast](https://github.com/ekristen/cast) -- installer cli
- [saltstack](https://github.com/teamdfir/sift-saltstack) -- states that actually do the work
- [packer](https://github.com/teamdfir/sift-packer) -- builds machine images using the above tools
- [package-scripts](https://github.com/teamdfir/package-scripts) -- builds certain packages hosted in [SIFT PPA](https://launchpad.net/~sift)

## Supported Distros

* 20.04 Ubuntu (Focal)
* 22.04 Ubuntu (Jammy)

## Installation

[Cast](https://github.com/ekristen/cast) is the replacement to the [SIFT CLI](https://github.com/sans-dfir/sift-cli). While the SIFT CLI should continue to work it is officially deprecated as of March 1, 2023 and will no longer be guaranteed to work after that date.

You must first install the CLI tool, then you can install SIFT.

```console
sudo cast install teamdfir/sift-saltstack
```

## Cloud Providers

### AWS

These are the latest AMIs build from [sift-packer](https://github.com/sans-dfir/sift-packer)

**Note:** these are headless, as in no GUI, it installs the server variant of SIFT.

### 22.04 Jammy Images

**Default User:** `sansforensics`

```
Account ID: 469658012540
Name: sans-sift-workstation-server-20240214124249
Regions:
  - eu-west-1 -> ami-02b8801c5dd864319
  - ap-southeast-1 -> ami-0a89fcec3f0d654f9
  - us-west-1 -> ami-0443a8664211c05f0
  - us-east-2 -> ami-04d0b46b95f792b67
  - ap-northeast-3 -> ami-049c6d359a6b056cc
  - eu-north-1 -> ami-00c969795f1510155
  - ap-northeast-2 -> ami-0d87d93a9fa3793e2
  - ca-central-1 -> ami-075fc1cf4efb61867
  - eu-west-3 -> ami-073eaa4931bcd39eb
  - eu-west-2 -> ami-0c494a1b9f9e341b1
  - eu-central-1 -> ami-0a50e71994d4ec832
  - ap-southeast-2 -> ami-0a52aae3e9bb5ff98
  - us-west-2 -> ami-0a6077f47a38022b7
  - us-east-1 -> ami-033658932fa06b1e6
  - ap-northeast-1 -> ami-09176a630354099ad
```

### 20.04 Focal Images

Built On: March 2nd, 2022

**Default User:** `sansforensics`

```
ap-northeast-1: ami-00378014d524eee9c
ap-northeast-2: ami-06408b1c23cad3f8b
ap-northeast-3: ami-0cf5998c0f77e349d
ap-southeast-1: ami-0db8ec4279e4f27ca
ap-southeast-2: ami-04c740d52b4a32959
eu-central-1: ami-06535b5a0f7d99f4c
eu-north-1: ami-049c42f0a1ea82701
eu-west-1: ami-01f1035b96448b73b
eu-west-2: ami-0407016f8aa79ea7c
eu-west-3: ami-0c444654c3cb65700
us-east-1: ami-0d52daefbb3dad017
us-east-2: ami-08faa4091f9e4121d
us-west-1: ami-0bf84579f13473e79
us-west-2: ami-0b9d5c33ff8f8ca7d
```
````
