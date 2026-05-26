def main():
    a: int = 0
    b: int = 0
    c: int = 0
    print("Digite A")
    a = int(input())
    print("Digite B")
    b = int(input())
    if a < b:
        c = b
    else:
        c = a
    print("Maior valor:")
    print(c)

if __name__ == '__main__':
    main()
