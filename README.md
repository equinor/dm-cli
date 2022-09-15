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

Reset applications connected to portal.
```
dm --dir ../create-dm-app/apps reset-app
```

If you want to see these options in the terminal, run `dm reset-app -h`. You could also run `dm -h` to see the available commands. (`reset-app` is the only command right now).

### Development

```
python3 -m venv .venv
source .venv/bin/activate
python3 setup.py install
dm --dir ../create-dm-app/apps reset-app
```

You need to have DMSS running locally.

### Feedback
Please feel free to leave feedback in issues/PRs.