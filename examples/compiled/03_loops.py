def main():
    i: int = 0
    soma: int = 0
    j: int = 0
    k: int = 0
    soma = 0
    i = 1
    while i <= 5:
        soma = soma + i
        i = i + 1
    print(soma)
    j = 1
    while j <= 3:
        print(j)
        j = j + 1
    k = 0
    while True:
        k = k + 2
        if not (k < 6):
            break
    print(k)

if __name__ == '__main__':
    main()
