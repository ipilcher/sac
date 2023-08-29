# Source Address Client

&copy; 2023 Ian Pilcher <<arequipeno@gmail.com>>

Listens for IPv4 source address announcements from the
[Source Address Daemon](https://github.com/ipilcher/sad) and reconfigures local
or remote resources when the source address changes.

* [**Installation**](#installation)
  * [Asterisk PJSIP plugin installation](#asterisk-pjsip-plugin-installation)
* [**Configuration**](#configuration)
* [**Running `sacd`**](#running-sacd)

## Installation

Build the SELinux policy module.  (Ignore any warnings about duplicate macro
definitions.)

```
$ make -f /usr/share/selinux/devel/Makefile
...
Compiling targeted sac module
Creating targeted sac.pp policy package
rm tmp/sac.mod tmp/sac.mod.fc
```

Install the policy module.

```
# semodule -i sac.pp
```

Create the `sac` user (and group).

```
# useradd -c 'Source Address Client' -d /tmp -M -r -s /usr/sbin/nologin sac
```

Install the Python modules.

```
# mkdir -p /usr/local/lib64/python3.11/site-packages
# cp -r sac /usr/local/lib64/python3.11/site-packages
```

Install the "executable."

```
# cp sacd /usr/local/bin/
# chmod 0755 /usr/local/bin/sacd
# restorecon /usr/local/bin/sacd
```

Install the systemd unit file.

```
# cp sac.service /etc/systemd/system/
```

If necessary, edit the unit file.  See the output of `sacd --help` for the
command line options.

Create the configuration directory.

```
# mkdir /etc/sac
# chown sac:sac /etc/sac
# chmod 0500 /etc/sac
# restorecon /etc/sac
```

> **NOTE:** The contents of the SAC configuration file should be protected, as
> it may contain credentials used to reconfigure remote services (such as
> Hurricane Electric dynamic DNS).

### Asterisk PJSIP plugin installation

The steps in this section are only needed if the Asterisk PJSIP plugin will be
used.

Install the `systemd-tmpfiles` configuration.

```
# cp sac_ast_pjsip.conf /etc/tmpfiles.d/
```

Apply the configuration to create the plugin's "state" directory.

```
# systemd-tmpfiles --create
```

Install the systemd unit files.

```
# cp asterisk-pjsip-reload.{path,service} /etc/systemd/system/
```

Edit the unit files, if necessary.

## Configuration

The configuration file (`/etc/sac/sac.conf` by default) is a
[TOML](https://toml.io/) document.  See the example file in this repository for
details of the settings.  Note the following.

* The configuration file is case sensitive.

* Strings (including IP addresses) ust be enclosed in single or double quotation
  marks.  (See the [TOML specification](https://toml.io/en/v1.0.0#string).)

* The `[listen]` and `[route]` sections are optional.  The default values and
  behavior should be correct in most cases.

* The `[plugins]` section is also technically optional.  If no plugins are
  configured, SAC will still listen for announcements, but it won't do anything
  (other than log a message) if the source address changes.

* Plugins must be both loaded **and** configured.

* The `modules` and `files` settings in the `[plugins]` section load (import)
  the Python modules that contain plugin classes.  (A plugin class is a Python
  class that extends `sac.plugin.Plugin`.

* Individual plugins are created and configured in their own configuration
  sections, named `[plugin.${name}]`.  For example, a section named
  `[plugin.asterisk]` creates a plugin named `asterisk`.

* Multiple instances of a plugin class can be created.  For example, two
  instances of the Huricane Electric DNS plugin (`HEDNSPlugin`) could be used
  to update the DNS records of two different hostnames.  (The names of the two
  plugins must be different, e.g. `[plugin.dns1]` and `[plugin.dns2]`.)

A minimal configuration that enables both the Hurricane Electric DNS and
Asterisk PJSIP plugins might look like this.

```ini
[plugins]
modules = [ 'sac.plugins.he_dns', 'sac.plugins.ast_pjsip' ]

[plugin.he-dns]
class = 'sac.plugins.he_dns.HEDNSPlugin'
username = '********'
password = '*************'
hostname = 'example.com'
nameservers = [
	'ns1.he.net',
	'ns2.he.net',
	'ns3.he.net',
	'ns4.he.net',
	'ns5.he.net'
]

[plugin.asterisk]
class = 'sac.plugins.ast_pjsip.AsteriskPJSIPPlugin'
```
## Running `sacd`

The SAC daemon (`sacd`) can be executed from the command line.  Running
`sacd --help` will show the available command line options.  If the daemon
detects that it has run from the command line (if `stderr` is a terminal), it
will send its log messages to `stderr`, rather than the system log.  (The
`--stderr` option can be used to force log messages to be sent to `stderr` when
it is not a terminal.  This is true when `stderr` has been piped to a program
such as `less`, for example.

Before running SAC as a service, enable the SELinux booleans required by the
plugins that will be used.

For the Hurricane Electric DNS plugin:

```
# setsebool -P sac_allow_http on
```

For the Asterisk PJSIP plugin:

```
# setsebool -P sac_allow_pjsip on
```
