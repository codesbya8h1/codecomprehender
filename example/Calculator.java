package com.example.calculator;

import java.util.Scanner;

public class Calculator {
    
    private double result;
    
    public Calculator() {
        this.result = 0.0;
    }
    
    public double add(double a, double b) {
        result = a + b;
        return result;
    }
    
    public double subtract(double a, double b) {
        result = a - b;
        return result;
    }
    
    public double multiply(double a, double b) {
        result = a * b;
        return result;
    }
    
    public double divide(double a, double b) {
        if (b == 0) {
            throw new IllegalArgumentException("Division by zero is not allowed");
        }
        result = a / b;
        return result;
    }
    
    public double getResult() {
        return result;
    }
    
    public void clear() {
        result = 0.0;
    }
    
    public double power(double base, double exponent) {
        result = Math.pow(base, exponent);
        return result;
    }
    
    public double sqrt(double number) {
        if (number < 0) {
            throw new IllegalArgumentException("Cannot calculate square root of negative number");
        }
        result = Math.sqrt(number);
        return result;
    }
    
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        Scanner scanner = new Scanner(System.in);
        
        System.out.println("Simple Calculator");
        System.out.println("Enter two numbers and an operation (+, -, *, /, ^, sqrt):");
        
        while (true) {
            System.out.print("Enter first number (or 'quit' to exit): ");
            String input = scanner.next();
            
            if (input.equalsIgnoreCase("quit")) {
                break;
            }
            
            try {
                double num1 = Double.parseDouble(input);
                
                System.out.print("Enter operation (+, -, *, /, ^, sqrt): ");
                String operation = scanner.next();
                
                double result = 0;
                
                if (operation.equals("sqrt")) {
                    result = calc.sqrt(num1);
                } else {
                    System.out.print("Enter second number: ");
                    double num2 = scanner.nextDouble();
                    
                    switch (operation) {
                        case "+":
                            result = calc.add(num1, num2);
                            break;
                        case "-":
                            result = calc.subtract(num1, num2);
                            break;
                        case "*":
                            result = calc.multiply(num1, num2);
                            break;
                        case "/":
                            result = calc.divide(num1, num2);
                            break;
                        case "^":
                            result = calc.power(num1, num2);
                            break;
                        default:
                            System.out.println("Invalid operation");
                            continue;
                    }
                }
                
                System.out.println("Result: " + result);
                
            } catch (NumberFormatException e) {
                System.out.println("Invalid number format");
            } catch (IllegalArgumentException e) {
                System.out.println("Error: " + e.getMessage());
            }
        }
        
        scanner.close();
        System.out.println("Calculator closed.");
    }
} 