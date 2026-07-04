def main() -> None:
    # 变量：给一个值起名字，后面可以用这个名字取出这个值。
    name = "Panpan"
    age = 25
    height = 1.75
    is_student = True
    phone = None

    print("=== 基本变量 ===")
    print("name:", name)
    print("age:", age)
    print("height:", height)
    print("is_student:", is_student)
    print("phone:", phone)

    print("\n=== 查看类型 ===")
    print("type(name):", type(name))
    print("type(age):", type(age))
    print("type(height):", type(height))
    print("type(is_student):", type(is_student))
    print("type(phone):", type(phone))

    print("\n=== Python 变量可以重新指向不同类型的值 ===")
    score = 100
    print("score:", score, "type:", type(score))

    score = "A+"
    print("score:", score, "type:", type(score))

    print("\n=== 类型转换 ===")
    user_input_age = "30"
    next_year_age = int(user_input_age) + 1
    print("user_input_age:", user_input_age, "type:", type(user_input_age))
    print("next_year_age:", next_year_age, "type:", type(next_year_age))

    price_text = "19.99"
    price = float(price_text)
    print("price:", price, "type:", type(price))

    print("\n=== 字符串拼接和格式化 ===")
    message = "name=" + name + ", age=" + str(age)
    print(message)

    better_message = f"name={name}, age={age}, height={height}"
    print(better_message)

    print("\n=== 布尔值常用于判断 ===")
    has_phone = phone is not None
    print("has_phone:", has_phone)


if __name__ == "__main__":
    main()
