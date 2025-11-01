
failing_tests = {
    "test_fail_1.txt": """i32 x{10}
i32 y{z + 5}
return y""",
    
    "test_fail_2.txt": """i32 x{10}
x = 20
return x""",
    
    "test_fail_3.txt": """i32 x{x + 5}
return x""",
    
    "test_fail_4.txt": """i32 x{10}
y = 15
return y""",
    
    "test_fail_5.txt": """i64 big{5000000000}
i32 small{big}
return small""",
    
    "test_fail_6.txt": """bool flag{true}
bool other{false}
i32 result{flag + other}
return result""",
    
    "test_fail_7.txt": """i32 x{10}
i32 y{20}
return x
return y""",
    
    "test_fail_8.txt": """i32 x{10}
i32 y{20} i32 z{30}
bool flag{true}
return x""",
    
    "test_fail_9.txt": """i32 x{10}
i32 x{20}
return x""",
    
    "test_fail_10.txt": """i32 x{10}
if x
{
    return 1
}
return 0""",
    
    "test_fail_11.txt": """i32 x{10}
bool y{!x}
return 0""",
    
    "test_fail_12.txt": """i32 x{10}
if true
{
    return 5
    x = 20
}
return 0""",
    
    "test_fail_13.txt": """i32 x{10}
if true
{
    i32 y{20}
}
return y""",
    
    "test_fail_14.txt": """i32 x{10}
if true
{
    x = 20

return x""",
    
    "test_fail_15.txt": """Point p{10, 20}
return 0""",
    
    "test_fail_16.txt": """struct Point
{
    i32 x
    i32 x
}

Point p{10, 20}
return 0""",
    
    "test_fail_17.txt": """struct Point
{
    UnknownType x
    i32 y
}

Point p{10, 20}
return 0""",
    
    "test_fail_18.txt": """struct Point
{
    i32 x
    i32 y
}

Point p{10, 20, 30}
return 0""",
    
    "test_fail_19.txt": """struct Point
{
    i32 x
    i32 y
}

Point p{true, 20}
return 0""",
    
    "test_fail_20.txt": """struct Point
{
    i32 mut x
    i32 mut y
}

Point p{10, 20}
p.x = 15
return 0""",
    
    "test_fail_21.txt": """struct Point
{
    i32 mut x
    i32 mut y
}

struct Circle
{
    Point center
    i32 mut radius
}

Point p{10, 20}
Circle mut c{p, 5}
c.center.x = 25
return 0""",
    
    "test_fail_22.txt": """struct Point
{
    i32 x
    i32 y
}

Point p{10, 20}
i32 z{p.z}
return z""",
    
    "test_fail_23.txt": """i32 x{10}
i32 y{x.field}
return y""",
    
    "test_fail_24.txt": """struct Point
{
    i32 x
    i32 y
}

Point p1{10, 20}
Point p2{30, 40}
bool result{p1 == p2}
return 0""",
    
    "test_fail_25.txt": """i32 result{add(5, 10)}
return result""",
    
    "test_fail_26.txt": """fn add = (i32 a, i32 b) -> i32
{
    return a + b
}

i32 result{add(5)}
return result""",
    
    "test_fail_27.txt": """fn add = (i32 a, i32 b) -> i32
{
    return a + b
}

i32 result{add(true, 10)}
return result""",
    
    "test_fail_28.txt": """fn getValue = () -> i32
{
    return true
}

i32 x{getValue()}
return x""",
    
    "test_fail_29.txt": """fn compute = (i32 x) -> i32
{
    i32 y{x + 5}
}

i32 result{compute(10)}
return result""",
    
    "test_fail_30.txt": """fn compute = (i32 x, i32 x) -> i32
{
    return x
}

i32 result{compute(5, 10)}
return result""",
    
    "test_fail_31.txt": """fn modify = (i32 x) -> i32
{
    x = x + 5
    return x
}

i32 result{modify(10)}
return result""",
    
    "test_fail_32.txt": """fn process = (UnknownType x) -> i32
{
    return 42
}

i32 result{process(10)}
return result""",
    
    "test_fail_33.txt": """fn getValue = () -> UnknownType
{
    return 42
}

i32 result{getValue()}
return result""",
    
    "test_fail_34.txt": """struct Circle
{
    Point center
    i32 radius
}

struct Point
{
    i32 x
    i32 y
}

Point p{10, 20}
Circle c{p, 5}
return 0""",
    
    "test_fail_35.txt": """i32 x{10}
i32 y{20}""",
    
    "test_fail_36.txt": """bool flag{true}
i32 num{5}
bool result{flag == num}
return 0""",
    
    "test_fail_37.txt": """struct Point
{
    i32 x
    i32 y
}

struct Point
{
    i32 a
    i32 b
}

Point p{10, 20}
return 0""",
    
    "test_fail_38.txt": """i32 mut x{10}
x = x
return x""",
    
    "test_fail_39.txt": """i32 mut x{10}
x = true
return x""",
    
    "test_fail_40.txt": """struct Point
{
    i32 x
    i32 y
}

struct Circle
{
    Point center
    i32 radius
}

Circle c{10, 20}
return 0""",
}

# Write all failing test files
import os

# Create test_cases directory if it doesn't exist
os.makedirs('test_cases', exist_ok=True)

for filename, content in failing_tests.items():
    filepath = os.path.join('test_cases', filename)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Created {filepath}")

print(f"\nSuccessfully created {len(failing_tests)} failing test files!")
