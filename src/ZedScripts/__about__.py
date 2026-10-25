from importlib.metadata import version

__version__ = version("ZedScripts")

def main():
    print(__version__)

if __name__ == "__main__":
    main()