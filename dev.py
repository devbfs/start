#!/usr/bin/env python
# encoding: utf-8

import sys
import subprocess

brew_packages = [
    "mercurial"
    ,"google-app-engine"
    ,"android-sdk"
    ,"android-ndk"
    ,"ant"
    ,"git"
    ,"ack"
    ,"perforce"
    ,"heroku-toolbelt"
    ,"vorbis-tools"
    ,"fontforge"
    ,"backflip-brew-tools"
    ,"backflip-engine-support"
]
homebrew_taps = [
    "homebrew/versions"
    ,"homebrew/binary"
    ,"homebrew/dupes"
    ,"devbfs/homebrew-formulas"
]
pip_packages = [
    ["docutils"]
    ,["PEAK-Rules", "--pre", "--allow-unverified", "PEAK-Rules"]
    ,["keyring"]
    ,["mercurial_keyring"]
    ,["pycrypto==2.6"]
    ,["boto"]
    ,["simplejson"]
    ,["sphinx"]
    ,["sphinxcontrib-googleanalytics"]
]
gem_packages = [
    "json"
    ,"open4"
    ,"rest-client"
    ,"facter"
    ,"systemu"
]

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

def validate_path():
    p1 = subprocess.Popen(["/usr/bin/env"], stdout=subprocess.PIPE, shell=False)
    p2 = subprocess.Popen(["grep", "PATH"], stdin=p1.stdout, stdout=subprocess.PIPE, shell=False)

    path, error = p2.communicate()
    if p2.returncode != 0:
        return False

    if path == None:
        return False

    idx1 = path.find("/usr/local/bin")
    idx2 = path.find("/usr/bin")

    if idx1 > idx2:
        return False

    return True
    
def main(args):
    clang = communicate(["xcrun", "clang", "--version"])
    if clang == None:
        print("ERROR: Xcode command line tools are not installed. Please install the command line tools before continuing")
        return 1

    brew = communicate(["brew", "--version"])
    if brew == None:
        print("ERROR: Homebrew was not found. Please install homebrew first:\n\nruby -e \"$(curl -fsSL https://raw.github.com/mxcl/homebrew/go/install)\"\n\nDon't forget to run brew doctor and resolve any issues before continuing.\n\n")
        return 1

    java = communicate(["java", "-version"])
    if java == None:
        print("ERROR: Please install java before continuing:\n\nhttp://support.apple.com/kb/DL1572?viewlocale=en_US\n\n")
        return 1

    if not validate_path():
        print("ERROR: /usr/bin occurs before /usr/local/bin.\n\nHere is a one-liner:\n\necho export PATH=\"/usr/local/bin:$PATH\" >> ~/.bash_profile\n")
        return 1

    ret = call(["brew", "doctor"])
    if ret != 0:
        print("WARNING: brew doctor returned error response. Please resolve all issues before continuing.")
        ask_or_exit(ret)

    print("Adding additional homebrew taps...")
    for tap in homebrew_taps:
        ret = call(["brew", "tap", tap])
        if ret != 0:
            print("WARNING: brew tap {} returned response: {}".format(tap, ret))
            ask_or_exit(ret)

    print("Updating Homebrew...")
    ret = call(["brew", "update"])
    if ret != 0:
        print("WARNING: brew update returned response: %d" % (ret))
        ask_or_exit(ret)

    print("Installing python...")
    brew_install("python", True)

    print("Installing ruby...")
    brew_install("ruby193", True)

    path = communicate(["which", "python"])
    if path == None or path != "/usr/local/bin/python":
        print("ERROR: Python environment is not configured properly. Ensure that /usr/local/bin is listed before /usr/bin in your PATH.")
        return 1

    path = communicate(["which", "ruby"])
    if path == None or path != "/usr/local/bin/ruby":
        print("ERROR: Ruby environment is not configured properly. Ensure that /usr/local/bin is listed before /usr/bin in your PATH.")
        return 1

    print("Installing BREW packages...")
    for brew_package in brew_packages:
        brew_install(brew_package, False)

    print("Installing PIP packages...")
    for pip_package in pip_packages:
        pip_install(pip_package, False)

    print("Installing GEM packages...")
    for gem_package in gem_packages:
        gem_install(gem_package, False)

    print("Running the Android SDK package installer...\n\nRequirements:\n\nTools:\n\tAndroid SDK Tools\n\tAndroid SDK Platform-tools\n\tAndroid SDK Build-tools\n\nAndroid APIs:\n\tSDK Platform for API 7 through the latest.\n\n")
    call(["android"])

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
