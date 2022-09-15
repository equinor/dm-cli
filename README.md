![](https://visitor-badge.glitch.me/badge?page_id=kanish671.ranpass)

# Data modelling CLI Tool

### Requirements
This package requires Python 3.

### Installing
To install this CLI tool you can run the below command
```
pip3 install dm
```

Alternatively, you clone this repo and then run this command from within the repository folder
```
python3 setup.py install
```

Both the above commands would install the package globally and `dm` will be available on your system.

### How to use

#### Portal
Load data for portal
```
dm portal -l <length of password desired> -o <option of password type>
```
There are four options for password type
1. Only lowercase alphabets
2. Lowercase + uppercase alphabets
3. Alphanumeric
4. Alphanumeric + Special characters (Default option, because passwords should be as secure as possible)

If you want to see these options in the terminal, run `ranpass generate -h`. You could also run `ranpass -h` to see the available commands. (`generate` is the only command right now).

### Develop

```
python3 -m venv .venv
source .venv/bin/activate
python3 setup.py install
```

### Feedback
Please feel free to leave feedback in issues/PRs.