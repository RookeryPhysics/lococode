def add_numbers(num1, num2, num3, num4, num5, num6):
  """Adds six numbers and returns the sum."""
  total = num1 + num2 + num3 + num4 + num5 + num6
  return total

if __name__ == "__main__":
  # Get input from the user
  try:
    num1 = float(input("Enter the first number: "))
    num2 = float(input("Enter the second number: "))
    num3 = float(input("Enter the third number: "))
    num4 = float(input("Enter the fourth number: "))
    num5 = float(input("Enter the fifth number: "))
    num6 = float(input("Enter the sixth number: "))
  except ValueError:
    print("Invalid input. Please enter numbers only.")
    exit()

  # Calculate the sum
  sum_of_numbers = add_numbers(num1, num2, num3, num4, num5, num6)

  # Print the result
  print("The sum of the six numbers is:", sum_of_numbers)