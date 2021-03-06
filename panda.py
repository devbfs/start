#!/usr/bin/env python
import argparse
import ConfigParser
import subprocess
import sys

from os import chdir, getcwd, mkdir
from os.path import expanduser, isdir, join
from socket import gethostname

agent_support = {
    'brew': [
        'androidndk-9c-android',
        'androidndk-9d-android',
        'androidndk-10d-android',
        'xcode-6.1.1-mac',
        'xcode-6.2-mac',
        'unity-4.6.3f1-mac',
        'unity-4.6.3p3-mac',
        'unity-5.0.0f4-mac'
    ],
    'gem': [
        'xcodeproj -v 0.19.2'
    ],
    'pip': [
        ['paramiko',
         'requests'
        ]
    ]
}

bamboo_support = {
    'brew': [
    ],
    'gem': [
    ],
    'pip': [
    ]
}

web_support = {
    'brew': [
    ],
    'gem': [
    ],
    'pip': [
    ]
}

gitconfig = '''
[credential "https://backflipstudios.kilnhg.com"]
username = {}
helper = store
'''

gitcredentials = '''
https://{}:{}@backflipstudios.kilnhg.com
'''

hgconfig = '''
[auth]
kiln.prefix = backflipstudios.kilnhg.com
kiln.username = {}
kiln.password = anypassword

[extensions]
purge =
'''

backflipbrewconfig = '''
[auth]
token={}
'''

profileconfig = '''
export PANDA_HOME={}/panda

alias la="ls -la"
'''

update_agent = '''
#/bin/sh
cd ~/panda
git pull origin agent
'''

clean_build_dir = '''
#/bin/sh
BUILD_DIR=~/bamboo-agent-home/xml-data/build-dir

echo "Clearing build dir: ${BUILD_DIR}"

cd $BUILD_DIR
pwd
rm -fr ./*

echo "Bamboo build dir clean completed."
'''

clean_build_dir_plist= '''
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.backflipstudios.cleanbuilddir</string>

        <key>ProgramArguments</key>
        <array>
            <string>/Users/bamboo/clear_build_dir.sh</string>
        </array>

        <key>StartCalendarInterval</key>
        <dict>
                <key>Minute</key><integer>0</integer>
                <key>Hour</key><integer>4</integer>
                <key>WeekDay</key><integer>6</integer>
        </dict>
    </dict>
</plist>
'''

bamboo_plist = '''
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.atlassian.bamboo</string>

        <key>UserName</key>
        <string>bamboo</string>

    <key>EnvironmentVariables</key>
        <dict>
            <key>PATH</key>  <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
            <key>PANDA_HOME</key>  <string>/Users/bamboo/panda/</string>
        </dict>

        <key>ProgramArguments</key>
        <array>
            <string>/Users/bamboo/bamboo-agent-home/bin/bamboo-agent.sh</string>
            <string>console</string>
        </array>

        <key>RunAtLoad</key>
        <true/>

        <key>SessionCreate</key>
        <true/>
    </dict>
</plist>
'''

emacsconfig = '''
;; no splash screen
(setq inhibit-splash-screen t)

;; no startup message
(setq inhibit-startup-message t)

;; make the initial scratch buffer empty
(setq initial-scratch-message "")

;; Enable delete selection
(delete-selection-mode t) 

;; no menu/tool/scroll bars
(if (fboundp 'menu-bar-mode) (menu-bar-mode -1))
(if (fboundp 'tool-bar-mode) (tool-bar-mode -1))
(if (fboundp 'scroll-bar-mode) (scroll-bar-mode -1))

;; show column number
(column-number-mode t)

;; only require 'y' and 'n', not 'yes' and 'no'
(fset 'yes-or-no-p 'y-or-n-p)

;; highlight matching parentheses
(show-paren-mode t)

;; highlight the line that point is on
(global-hl-line-mode t)

;; reload files if they change
(global-auto-revert-mode 1)

;; tab settings
(setq-default tab-width 4)
(setq-default indent-tabs-mode nil)
(setq c-default-style "k&r")
(setq c-basic-offset 4)

;; line numbers
(require 'linum)
(global-linum-mode t)
(setq linum-format "%4d\u2502 ")

;; backups
(setq backup-by-copying t)
(setq backup-directory-alist `(("." . "~/.emacs.backups/")))
(setq auto-save-list-file-prefix "~/.emacs.backups/")
(setq auto-save-file-name-transforms `((".*" "~/.emacs.backups/" t)))
'''


def communicate(args):
    result = None
    try:
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        output, error = process.communicate()
        if process.returncode == 0:
            result = output.strip()
    except Exception:
        pass
    return result


def call(args):
    ret = subprocess.call(args)
    return ret


def ask_or_exit(ret):
    while True:
        choice = raw_input('Continue? (y/n): ')
        if choice == 'y' or choice == 'Y':
            break
        elif choice == 'n' or choice == 'N':
            print('Aborting.')
            sys.exit(ret)


def install_call(args, fail_on_error, quiet=False):
    ret = call(args)
    if ret != 0:
        print('\nERROR: Failed to install package: {}'.format(args))
        if fail_on_error:
            sys.exit(ret)
        elif not quiet:
            ask_or_exit(ret)
    

def brew_install(package_name, fail_on_error, quiet=False):
    install_call(["brew", "install"] + package_name.split(), fail_on_error, quiet)


def pip_install(package_props, fail_on_error, quiet=False):
    install_call(["pip", "install"] + package_props, fail_on_error, quiet)


def gem_install(package_name, fail_on_error, quiet=False):
    install_call(["gem", "install"] + package_name.split(), fail_on_error, quiet)


def write_config(path, content):
    with open(expanduser(path), 'w') as f:
        f.write(content)


def write_profile_config():
    write_config('~/.profile', profileconfig.format(expanduser('~')))


def write_kiln_config(config_parser):
    if config_parser:
        # Get the first part of the hostname if the fully qualified domain name is used. This gives us 'red-panda1' if
        # the FQDN is 'red-panda1.backflipstudios.com'.
        hostname = gethostname().split('.')[0]
        try:
            kiln_access_token = config_parser.get('kiln', hostname)
        except ConfigParser.NoOptionError:
            print 'ERROR: Hostname does not match any values in .tokens.'
            sys.exit(1)
    else:
        kiln_access_token = raw_input('Kiln Access Token: ')

    if kiln_access_token is not None and len(kiln_access_token) > 0:
        write_config('~/.hgrc', hgconfig.format(kiln_access_token))
        write_config('~/.gitconfig', gitconfig.format(kiln_access_token))
        write_config('~/.git-credentials', gitcredentials.format(kiln_access_token, 'anypassword'))


def write_github_config(config_parser):
    if config_parser:
        github_access_token = config_parser.get('github', 'token')
    else:
        github_access_token = raw_input('Github Access Token: ')

    if github_access_token is not None and len(github_access_token) > 0:
        write_config('~/.backflipbrew', backflipbrewconfig.format(github_access_token))
   

def write_plists():
    launchagent_path = '~/Library/LaunchAgents/'
    print('Installing launch agents to {}...'.format(launchagent_path))
    if not isdir(expanduser(launchagent_path)):
        mkdir(expanduser(launchagent_path))

    write_config(join(launchagent_path, 'com.atlassian.bamboo.plist'), bamboo_plist)
    write_config(join(launchagent_path, 'com.backflipstudios.cleanbuilddir.plist'), clean_build_dir_plist)


def write_shell_scripts():
    print('Installing support scripts to ~/...')
    write_config(join('~', 'update_agent.sh'), update_agent)
    write_config(join('~', 'clear_build_dir.sh'), clean_build_dir)


def clone_panda_repo():
    print('Cloning the panda repository...')
    current_dir = getcwd()
    chdir(expanduser('~'))
    install_call(['git', 'clone', 'https://backflipstudios.kilnhg.com/Code/Repositories/Group/panda.git'], False)
    chdir('panda')
    install_call(['git', 'checkout', 'agent'], False)
    chdir(current_dir)


def accept_unity_license():
    pass


def xcode_select():
    pass


def install_developer_certificate():
    pass


def main():
    parser = argparse.ArgumentParser(description='Panda Build System setup script.')
    parser.add_argument('-e', '--emacs', help='Install/configure basic emacs setup', action='store_true', required=False)
    parser.add_argument('-a', '--agent', help='Install Agent (red-panda) support', action='store_true', required=False)
    parser.add_argument('-b', '--bamboo', help='Install Bamboo (panda) support', action='store_true', required=False)
    parser.add_argument('-w', '--web', help='Install Web (kungfu) support', action='store_true', required=False)
    parser.add_argument('-i', '--environment', help='Configure basic environment profile', action='store_true', required=False)
    parser.add_argument('-k', '--kiln', help='Configure git and mercurial to use Kiln Access Tokens', action='store_true', required=False)
    parser.add_argument('-g', '--github', help='Configure to use Github Access Tokens for Homebrew', action='store_true', required=False)
    parser.add_argument('-q', '--quiet', help='Quiet mode. Suppresses error messages from most failed installations.',
                        action='store_true', required=False)
    args = parser.parse_args()

    config = ConfigParser.SafeConfigParser()
    try:
        with open(expanduser('/.tokens')) as f:
            config.readfp(f)
    except IOError:
        config = None

    if not args.emacs and not args.agent and not args.bamboo and not args.web and not args.environment and not args.kiln and not args.github:
        parser.print_help()
        return 1

    if args.environment:
        print('Installing basic environment profile...')
        write_profile_config()

    if args.kiln:
        print('Setting up SCM for Kiln...')
        write_kiln_config(config)

    if args.github:
        print('Setting Github for Homebrew...')
        write_github_config(config)

    if args.emacs:
        print('Installing basic emacs setup...')
        brew_install('emacs', False)
        write_config('~/.emacs', emacsconfig)

    if args.agent:
        clone_panda_repo()
        write_plists()
        write_shell_scripts()

        print('Installing Xcode support...')
        for brew_package in agent_support['brew']:
            brew_install(brew_package, False, args.quiet)

        for pip_package in agent_support['pip']:
            pip_install(pip_package, False, args.quiet)

        for gem_package in agent_support['gem']:
            gem_install(gem_package, False, args.quiet)

    if args.bamboo:
        print('Installing Xcode support...')
        for brew_package in bamboo_support['brew']:
            brew_install(brew_package, False, args.quiet)

        for pip_package in bamboo_support['pip']:
            pip_install(pip_package, False, args.quiet)

        for gem_package in bamboo_support['gem']:
            gem_install(gem_package, False, args.quiet)

    if args.web:
        print('Installing Xcode support...')
        for brew_package in web_support['brew']:
            brew_install(brew_package, False, args.quiet)

        for pip_package in web_support['pip']:
            pip_install(pip_package, False, args.quiet)

        for gem_package in web_support['gem']:
            gem_install(gem_package, False, args.quiet)

    return 0

if __name__ == '__main__':
    sys.exit(main())

