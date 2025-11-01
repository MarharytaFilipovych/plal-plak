"""Script to generate all 40 test files for the compiler"""

tests = {
    "test_1.txt": """i32 x{10}
return x""",
    
    "test_2.txt": """i32 a{5}
i32 b{3}
i32 c{a + b}
return c""",
    
    "test_3.txt": """i32 mut x{10}
x = 20
return x""",
    
    "test_4.txt": """i32 a{100}
i32 b{50}
i32 mut result{a - b}
result = result * 2
return result""",
    
    "test_5.txt": """i32 x{-15}
i32 y{25}
i32 z{x + y}
return z""",
    
    "test_6.txt": """// This is a test
i32 value{42}

// Calculate result
i32 result{value * 2}
return result""",
    
    "test_7.txt": """i64 big{5000000000}
i32 small{100}
i64 sum{big + small}
bool isEqual{sum == 5000000100}
i32 mut counter{0}
counter = counter + 1
return counter""",
    
    "test_8.txt": """i32 a{100}
i64 b{a}
i64 c{a + 50}
return c""",
    
    "test_9.txt": """i32 x{15}
i32 y{20}
bool result{x == y}
bool check{x != y}
return check""",
    
    "test_10.txt": """i64 big{5000000000}
i32 small{100}
i64 sum{big + small}
bool isEqual{sum == 5000000100}
return isEqual""",
    
    "test_11.txt": """i32 small{100}
i64 large{100}
bool areEqual{small == large}
return areEqual""",
    
    "test_12.txt": """i32 x{10}
i64 y{20}
bool flag{true}
return x""",
    
    "test_13.txt": """i32 x_a1{10}
return x_a1""",
    
    "test_14.txt": """i32 mut x{5}
if true
{
    x = 10
}
return x""",
    
    "test_15.txt": """i32 mut x{5}
if false
{
    x = 10
}
return x""",
    
    "test_16.txt": """i32 mut x{5}
if x == 5
{
    x = 100
}
else
{
    x = 200
}
return x""",
    
    "test_17.txt": """bool a{true}
bool b{!a}
if b
{
    return 0
}
return 1""",
    
    "test_18.txt": """bool flag{false}
i32 mut result{0}
if !flag
{
    result = 42
}
return result""",
    
    "test_19.txt": """i32 x{10}
if true
{
    i32 x{20}
    return x
}
return x""",
    
    "test_20.txt": """i32 mut x{5}
if x == 5
{
    if true
    {
        x = 100
    }
    else
    {
        x = 50
    }
}
return x""",
    
    "test_21.txt": """i32 x{10}
if x == 10
{
    return 999
}
return 0""",
    
    "test_22.txt": """bool flag{true}
if flag
{
    return 1
}
else
{
    return 0
}
return -1""",
    
    "test_23.txt": """i32 x{10}
if true
{
    bool x{true}
    if x
    {
        return 5
    }
}
return x""",
    
    "test_24.txt": """struct Point
{
    i32 mut x
    i32 mut y
}

Point p{10, 20}
return 42""",
    
    "test_25.txt": """struct Point
{
    i32 mut x
    i32 mut y
}

Point p{10, 20}
i32 xCoord{p.x}
return xCoord""",
    
    "test_26.txt": """struct Point
{
    i32 mut x
    i32 mut y
}

Point mut p{10, 20}
p.x = 15
i32 result{p.x}
return result""",
    
    "test_27.txt": """struct Point
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
Circle c{p, 5}
return 100""",
    
    "test_28.txt": """struct Point
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
Circle c{p, 5}
i32 coord{c.center.x}
return coord""",
    
    "test_29.txt": """struct Point
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
c.radius = 10
i32 result{c.radius}
return result""",
    
    "test_30.txt": """struct Data
{
    i32 mut count
    i64 mut bigNum
    bool mut flag
}

Data d{42, 5000000000, true}
i32 result{d.count}
return result""",
    
    "test_31.txt": """fn getNumber = () -> i32
{
    return 42
}

i32 result{getNumber()}
return result""",
    
    "test_32.txt": """fn double = (i32 x) -> i32
{
    i32 result{x * 2}
    return result
}

i32 num{double(5)}
return num""",
    
    "test_33.txt": """fn add = (i32 a, i32 b) -> i32
{
    return a + b
}

i32 result{add(10, 20)}
return result""",
    
    "test_34.txt": """fn add = (i32 a, i32 b) -> i32
{
    return a + b
}

i32 c{add(5, add(3, 2))}
return c""",
    
    "test_35.txt": """fn max = (i32 a, i32 b) -> i32
{
    i32 mut result{a}
    if b == 10
    {
        result = b
    }
    return result
}

i32 answer{max(5, 10)}
return answer""",
    
    "test_36.txt": """fn isZero = (i32 x) -> bool
{
    return x == 0
}

bool result{isZero(0)}
return result""",
    
    "test_37.txt": """fn compute = (i32 x, bool flag) -> i32
{
    i32 mut result{x}
    if flag
    {
        result = result + 10
    }
    return result
}

i32 answer{compute(5, true)}
return answer""",
    
    "test_38.txt": """fn addOne = (i32 x) -> i32
{
    return x + 1
}

fn addTwo = (i32 x) -> i32
{
    return x + 2
}

i32 a{addOne(5)}
i32 b{addTwo(5)}
i32 result{a + b}
return result""",
    
    "test_39.txt": """i32 a{5}
i32 b{10}
i32 c{15}
i32 result{a + b * c - a}
return result""",
    
    "test_40.txt": """struct Point
{
    i32 mut x
    i32 mut y
}

fn distance = (Point p) -> i32
{
    i32 x{p.x}
    i32 y{p.y}
    return x + y
}

Point mut p{10, 20}
p.x = 15

i32 dist{distance(p)}
return dist""",
}

# Write all test files
import os

# Create test_cases directory if it doesn't exist
os.makedirs('test_cases', exist_ok=True)

for filename, content in tests.items():
    filepath = os.path.join('test_cases', filename)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Created {filepath}")

print(f"\nSuccessfully created {len(tests)} test files!")
