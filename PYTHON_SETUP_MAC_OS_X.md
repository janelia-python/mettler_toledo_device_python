Python Setup Mac OS X
=====================

Download and install XCode:

<https://developer.apple.com/xcode/>

Install Homebrew:

```shell
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```

Insert Homebrew directory at the top of the PATH by adding the
following line to the bottom of your ~/.profile file (create it if it
does not exist):

```shell
export PATH=/usr/local/bin:/usr/local/sbin:$PATH
```

Open a new terminal to complete the PATH modification or run:

```shell
source ~/.profile
```

Install Python 2.7, virtualenv, and ipython:

```shell
brew install python
pip install virtualenv
pip install ipython
```

Make a directory to store virtual environments:

```shell
mkdir ~/virtualenvs
```
