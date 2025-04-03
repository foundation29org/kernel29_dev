def separator(n=0, char="=", new_line=False):
    if new_line:
        print("\n" * n)
    else:
        print(char * 100 + "\n" * n)