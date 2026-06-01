from setuptools import setup

APP = ["ui/app.py"]

DATA_FILES = [
    ("", ["icon.icns"])
]

OPTIONS = {

    "argv_emulation": False,

    "iconfile": "icon.icns",

    "packages": [
        "customtkinter"
    ],

    "plist": {

        "CFBundleName": "Job Finder",

        "CFBundleDisplayName": "Job Finder",

        "CFBundleIdentifier":
        "com.jobfinder.app",

        "CFBundleVersion": "1.0.0",

        "CFBundleShortVersionString":
        "1.0.0",

        "NSHighResolutionCapable": True
    }
}

setup(

    app=APP,

    name="Job Finder",

    data_files=DATA_FILES,

    options={
        "py2app": OPTIONS
    },

    setup_requires=[
        "py2app"
    ]
)