#!/usr/bin/env python
# encoding: utf-8

import sys
import subprocess
import argparse
from os import chdir, getcwd
from os.path import expanduser

agent_support = {
    "brew" : [
        "androidndk-9c-android"
        ,"androidndk-9d-android"
        ,"xcode-5.0.2-mac"
        ,"xcode-5.1-mac"
        ,"xcode-5.1.1-mac"
        ,"xcode-6.0-mac"
        ,"unity-4.3.4f1-mac"
        ,"unity-4.5.0f6-mac"
    ],
    "gem" : [
        "xcodeproj"
    ],
    "pip" : [
        ["paramiko"
         ,"requests"
        ]
    ]
}

bamboo_support = {
    "brew" : [
    ],
    "gem" : [
    ],
    "pip" : [
    ]
}

web_support = {
    "brew" : [
    ],
    "gem" : [
    ],
    "pip" : [
    ]
}

gitconfig = '''
[credential "https://backflipstudios.kilnhg.com"]
username = {}
helper = osxkeychain
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
    except Exception, e:
        pass
    return result

def call(args):
    ret = subprocess.call(args)
    # if ret != 0:
    #     print("WARNING: subprocess  call (%s) returned %d" % (args, ret))
    return ret

def ask_or_exit(ret):
    while True:
        choice = raw_input("Continue? (y/n): ")
        if choice == "y" or choice == "Y":
            break
        elif choice == "n" or choice == "N":
            print("Aborting.")
            sys.exit(ret)

def install_call(args, fail_on_error):
    ret = call(args)
    if ret != 0:
        print("\nERROR: Failed to install package: %s" % (args))
        if fail_on_error:
            sys.exit(ret)
        else:
            ask_or_exit(ret)
    
def brew_install(package_name, fail_on_error):
    install_call(["brew", "install", package_name], fail_on_error)
    
def pip_install(package_props, fail_on_error):
    install_call(["pip", "install"] + package_props, fail_on_error)
    
def gem_install(package_name, fail_on_error):
    install_call(["gem", "install", package_name], fail_on_error)

def write_config(path, content):
    with open(expanduser(path), "w") as f:
        f.write(content)

def write_profile_config():
    write_config("~/.profile", profileconfig.format(expanduser("~")))

def write_kiln_config():
    kiln_access_token = raw_input("Kiln Access Token: ")
    if kiln_access_token is not None and len(kiln_access_token) > 0:
        write_config("~/.hgrc", hgconfig.format(kiln_access_token))
        write_config("~/.gitconfig", gitconfig.format(kiln_access_token))

def write_github_config():
    github_access_token = raw_input("Github Access Token: ")
    if github_access_token is not None and len(github_access_token) > 0:
        write_config("~/.backflipbrew", backflipbrewconfig.format(github_access_token))
   
def main(args):
    parser = argparse.ArgumentParser(description="Panda Build System setup script.")
    parser.add_argument("-e", "--emacs", help="Install/configure basic emacs setup", action="store_true", required=False)
    parser.add_argument("-a", "--agent", help="Install Agent (redpanda) support", action="store_true", required=False)
    parser.add_argument("-b", "--bamboo", help="Install Bamboo (panda) support", action="store_true", required=False)
    parser.add_argument("-w", "--web", help="Install Web (kungfu) support", action="store_true", required=False)
    parser.add_argument("-i", "--environment", help="Configure basic environment profile", action="store_true", required=False)
    parser.add_argument("-k", "--kiln", help="Configure git and mercurial to use Kiln Access Tokens", action="store_true", required=False)
    parser.add_argument("-g", "--github", help="Configure to use Github Access Tokens for Homebrew", action="store_true", required=False)
    args = parser.parse_args()

    if not args.emacs and not args.agent and not args.bamboo and not args.web and not args.environment and not args.kiln and not args.github:
        parser.print_help()
        return 1

    if args.environment:
        print("Installing basic environment profile...")
        write_profile_config()

    if args.kiln:
        print("Setting up SCM for Kiln...")
        write_kiln_config()

    if args.github:
        print("Setting Github for Homebrew...")
        write_github_config()

    if args.emacs:
        print("Installing basic emacs setup...")
        brew_install("emacs", False)
        write_config("~/.emacs", emacsconfig)

    if args.agent:
        # Agents need a couple versions of the Android NDK.
        # print('Installing NDK versions...')
        current_dir = getcwd()
        brew_path = communicate(['brew', '--prefix'])
        chdir(brew_path)
        # r9c
        install_call(['git', 'checkout', 'f284cac', 'Library/Formula/android-ndk.rb'], False)
        install_call(['brew', 'unlink', 'android-ndk'], False)
        install_call(['brew', 'install', 'android-ndk'], False)
        # and r9
        install_call(['git', 'checkout', 'a30d082', 'Library/Formula/android-ndk.rb'], False)
        install_call(['brew', 'unlink', 'android-ndk'], False)
        install_call(['brew', 'install', 'android-ndk'], False)

        install_call(['git', 'checkout', '--', 'Library/Formula/android-ndk.rb'], False)
        chdir(current_dir)

        print('Cloning the panda repository...')
        chdir(expanduser('~'))
        install_call(['git', 'clone', 'https://backflipstudios.kilnhg.com/Code/Repositories/Group/panda.git'], False)
        chdir('panda')
        install_call(['git', 'checkout', 'agent'], False)
        chdir(current_dir)

        print("Installing Xcode support...")
        for brew_package in agent_support["brew"]:
            brew_install(brew_package, False)

        for pip_package in agent_support["pip"]:
            pip_install(pip_package, False)

        for gem_package in agent_support["gem"]:
            gem_install(gem_package, False)

    if args.bamboo:
        print("Installing Xcode support...")
        for brew_package in bamboo_support["brew"]:
            brew_install(brew_package, False)

        for pip_package in bamboo_support["pip"]:
            pip_install(pip_package, False)

        for gem_package in bamboo_support["gem"]:
            gem_install(gem_package, False)

    if args.web:
        print("Installing Xcode support...")
        for brew_package in web_support["brew"]:
            brew_install(brew_package, False)

        for pip_package in web_support["pip"]:
            pip_install(pip_package, False)

        for gem_package in web_support["gem"]:
            gem_install(gem_package, False)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))

