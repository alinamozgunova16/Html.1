import sys
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLineEdit, QMessageBox, QFontComboBox, QSpinBox, QFileDialog, QInputDialog
from PySide6.QtGui import QFont, QIcon, QImage, QKeySequence, QAction, QActionGroup, QTextDocument, QTextCharFormat, QTextCursor

from interpreter import Ui_MainWindow

variables = {}

class Interpretator(QMainWindow):
    def __init__(self) -> None:
        super(Interpretator, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.text: str
        self.ui.pushButton_gen.clicked.connect(self.click_button)
        self.ui.pushButton_load.clicked.connect(self.get_text)

    def eval_expression(self, expr):
        expr = expr.replace("TRUE", "True").replace("FALSE", "False")
    

        for var_name, value in variables.items():
            expr = expr.replace(var_name, str(value))
    
        try:
            return eval(expr, {'builtins': None}, {})
        except Exception as e:
            print(f"Ошибка в выражении: {e}")
            return None

    def interpret(self, lines):
        results = []  
        i = 0
   
        def execute_line(line):
            nonlocal i
            line = line.strip()
       
            if line.startswith("show(") and line.endswith(")"):
            
                expression = line[5:-1]
                if expression in variables:
                    result = variables[expression]
                else:
                    result = self.eval_expression(expression)
                if result is not None:
                    results.append(result)
               
            elif "=" in line:
                
                var_name, expr = map(str.strip, line.split("=", 1))
                
                if expr.startswith("[") and expr.endswith("]"):
                
                    array_expr = expr[1:-1].strip()  
                    elements = array_expr.split(",") if array_expr else []
                    evaluated_elements = [self.eval_expression(e.strip()) for e in elements]
                    variables[var_name] = evaluated_elements
                else:
                
                    var_value = self.eval_expression(expr)
                    if var_value is not None:
                        variables[var_name] = var_value
        
            elif line.startswith("input"):
                # Ввод значения пользователем
                var_name = line[6:].strip()
                if var_name.isidentifier():
                    user_input, text = QInputDialog.getText(self, "Ввод переменной", f"Введите значение для переменной '{var_name}':")
                    # simpledialog.askstring("Ввод переменной", f"Введите значение для переменной '{var_name}':")
                    if user_input is not None:
                        try:
                            # Попробуем преобразовать ввод в число, если это возможно
                            value = eval(user_input, {"builtins": None}, {})
                        except Exception:
                            value = user_input  # Если не получилось, оставляем ввод как строку
                        variables[var_name] = value
                    else:
                        print(f"Ошибка: Ввод для переменной '{var_name}' отменён.")
                else:
                    print(f"Ошибка: '{var_name}' не является допустимым именем переменной.")
                    
            elif line.startswith("if"):
            
                condition = line[3:]
                if self.eval_expression(condition):
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith("endif"):
                        execute_line(lines[i])
                        i += 1
                else:
                    while i < len(lines) and not lines[i].strip().startswith("endif"):
                        i += 1
        
            elif line.startswith("while"):
        
                condition = line[6:]
                start_loop = i
                while self.eval_expression(condition):
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith("endwhile"):
                        execute_line(lines[i])
                        i += 1
                    i = start_loop
                while i < len(lines) and not lines[i].strip().startswith("endwhile"):
                    i += 1
                    
            elif line.startswith("for"):
                try:
                    parts = line[4:].split(" until ")
                    var_part, end_value = parts[0], self.eval_expression(parts[1])
                    var_name, start_value = map(str.strip, var_part.split("=", 1))
                    start_value = self.eval_expression(start_value)
            
                    if var_name not in variables:                    
                        variables[var_name] = start_value
                        start_index = i + 1
                        end_index = start_index
                        while end_index < len(lines) and not lines[end_index].strip().startswith("endfor"):
                            end_index += 1
                        for val in range(start_value, end_value + 1): 
                            variables[var_name] = val
                            loop_index = start_index
                        while loop_index < end_index:
                            execute_line(lines[loop_index])
                            loop_index += 1
                    
                    i = end_index  
                except Exception as e:
                    print(f"Ошибка в цикле для: {e}")
                
                while i < len(lines) and not lines[i].strip().startswith("endfor"):
                    i += 1

            elif line.startswith("add"):
            
                parts = line[4:].split(" in ")
                value_expr, array_name = map(str.strip, parts)
                value = self.eval_expression(value_expr)
                if array_name in variables and isinstance(variables[array_name], list):
                    variables[array_name].append(value)
                else:
                    print(f"Ошибка: {array_name} не является массивом или не существует.")
                    
            elif line.startswith("delete"):
            
                parts = line[7:].split(" from ")
                index_expr, array_name = map(str.strip, parts)
                index = self.eval_expression(index_expr)
                if array_name in variables and isinstance(variables[array_name], list):
                    try:
                        variables[array_name].pop(index)
                    except IndexError:
                        print(f"Ошибка: Индекс {index} вне диапазона для массива {array_name}.")
                else:
                    print(f"Ошибка: {array_name} не является массивом или не существует.")
                    
            elif line.startswith("get"):
            
                parts = line[4:].split(" from ")
                index_expr, array_name = map(str.strip, parts)
                index = self.eval_expression(index_expr)
                if array_name in variables and isinstance(variables[array_name], list):
                    try:
                        result = variables[array_name][index]
                        results.append(result)
                    except IndexError:
                        print(f"Ошибка: Индекс {index} вне диапазона для массива {array_name}.")
                else:
                    print(f"Ошибка: {array_name} не является массивом или не существует.")
    
        while i < len(lines):
            execute_line(lines[i])
            i += 1
        return results

    def get_text(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить данные", "", "Text Files (*.txt);;All Files (*)", options=options
        )
        if file_path:
            with open(file_path, "r") as file:
                line = file.read()
        self.text = line
        self.ui.textBrowser_input.setText(line)

    def click_button(self):
        """Handles button click to execute the user's code."""
        self.ui.textBrowser_output.clear()
        text2 = self.text
        lines = text2.splitlines()
        global variables 
        variables = {}
        code = self.interpret(lines)
        print("Переменные:", variables)  
        final = list(map(str, code))
        for i in final:
            self.ui.textBrowser_output.append(i+'\n')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Interpretator()
    window.show()
    sys.exit(app.exec())