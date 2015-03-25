#!/usr/bin/env python
import re
import sys
import subprocess

brew_packages = [
    "mercurial"
    ,"google-app-engine"
    ,"android-sdk"
    ,"android-ndk"
    ,"ant"
    ,"git"
    ,"perforce"
    ,"heroku-toolbelt"
    ,"vorbis-tools"
    ,"Caskroom/cask/xquartz"
    ,"fontforge"
    ,"webp"
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
    ,["PEAK-Rules==0.5a1.dev-r2707", "--pre", "--allow-unverified", "PEAK-Rules"]
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

def communicate(args, exit_on_error=True, **kwargs):
    input_data = kwargs['input'] if 'input' in kwargs else None

    p = subprocess.Popen(args,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=(kwargs['cwd'] if 'cwd' in kwargs else None))

    stdout_data, stderr_data = p.communicate(input=input_data)

    if p.returncode != 0:
        logger.error(' '.join(args))
        logger.error('{}'.format(stderr_data.rstrip()))

        if exit_on_error:
            sys.exit(1)
        else:
            return stderr_data

    return stdout_data.strip()

def call(args):
    ret = subprocess.call(args)
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

    if path is None:
        return False

    idx1 = path.find("/usr/local/bin")
    idx2 = path.find("/usr/bin")

    if idx1 > idx2:
        return False

    return True
    
def main():
    clang = communicate(["xcrun", "clang", "--version"])
    if clang is None:
        print("ERROR: Xcode command line tools are not installed. Please install the command line tools before continuing.")
        return 1

    brew = communicate(["brew", "--version"])
    if brew is None:
        print("ERROR: Homebrew was not found. Please install homebrew first:\n\nruby -e \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)\"\n\nDon't forget to run brew doctor and resolve any issues before continuing.\n\n")
        return 1

    java = communicate(["java", "-version"])
    if java is None:
        print("ERROR: Please install java before continuing:\n\nhttp://support.apple.com/kb/DL1572?viewlocale=en_US\n\n")
        return 1

    if not validate_path():
        print("ERROR: /usr/bin occurs before /usr/local/bin.\n\nHere is a one-liner:\n\necho export PATH=\"/usr/local/bin:$PATH\" >> ~/.bash_profile\n")
        return 1

    print("Updating Homebrew...")
    ret = call(["brew", "update"])
    if ret != 0:
        print("WARNING: brew update returned response: %d" % (ret))
        ask_or_exit(ret)

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

    print("Installing python...")
    brew_install("python", True)

    print("Installing ruby...")
    brew_install("ruby193", True)

    path = communicate(["which", "python"])
    if path is None or path != "/usr/local/bin/python":
        print("ERROR: Python environment is not configured properly. Ensure that /usr/local/bin is listed before /usr/bin in your PATH.")
        return 1

    path = communicate(["which", "ruby"])
    if path is None or path != "/usr/local/bin/ruby":
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

    install_android_sdk_packages()

    return 0


def install_android_sdk_packages():
    packages = list_sdk_packages()

    # Install the latest Android SDK tools.
    install_package_by_name('tool')

    # Install the latest Android SDK Platform-tools.
    install_package_by_name('platform-tool')

    # Install all versions of the SDK starting with API 7.
    for x in range(7, get_latest_sdk_version(packages) + 1):
        install_package_by_name('android-{}'.format(x))

    # Install the latest Build tools.
    install_package_by_name('build-tools-{}'.format(get_latest_build_tools_version(packages)))


def list_sdk_packages():
    args = [
        'android',
        'list',
        'sdk',
        '-a',
        '-e'
    ]
    return communicate(args)


def install_package_by_name(filter_name):
    print 'Installing {}.'.format(filter_name)
    args = [
        'android',
        'update',
        'sdk',
        '-u',
        '-a',
        '-t',
        filter_name
    ]
    print communicate(args, input="y")


def get_latest_build_tools_version(packages):
    # Build tools doesn't have its own filter so we have to find the latest version ourselves.
    return re.search('(?<="build-tools-)\d+\.\d+\.\d+', packages).group()


def get_latest_sdk_version(packages):
    # Search through the output to find the latest version of the sdk.
    # This matches any number of digits only if it's preceded by the string '"android-'.
    return int(re.search('(?<="android-)\d+', packages).group())


if __name__ == '__main__':
    sys.exit(main())
