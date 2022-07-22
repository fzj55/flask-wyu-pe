#有序的数组a 元素b b是否在a里面

a = [1,2,3,4]
b = 4

def fun(a,b):
    if len(a) == 1 and b != a[0]:
        return 'False'
    else:
        if b == a[int(len(a)/2)]:
            return 'True'
        elif b > a[int(len(a)/2)]:
           return fun(a[int(len(a)/2):],b)
        elif b < a[int(len(a)/2)]:
            return fun(a[:int(len(a) / 2)], b)

print(fun(a,b))


def binarySearch(a , n , target):
    mid = 0
    low = 0
    high = n - 1
    while low <= high :
        mid = (low + high) /2
# 将浮点型转换为整型
        mid = int(mid)
        if a[mid] == target:
            return mid
        elif a[mid] > target:
            high = mid - 1
        else:
            low = mid + 1
            return -1
a = [1,3,6,12,21,29,31,46,57,88,99];

index = binarySearch(a ,11 ,88);

print( index )