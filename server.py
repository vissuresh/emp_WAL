from flask import Flask, request
import json

app = Flask(__name__)
with open('./home/emp_count.txt') as emp_count:
    try:    
        emp_counter = int(emp_count.readline().strip('\n')) + 1
    except:
        pass

# Greeting 
@app.route("/greeting", methods=['GET'])
def greeting():
    return 'Hello world!'   

# Create Employee
@app.route('/employee', methods=['POST'])
def create_employee():
    new_emp = json.loads(request.data)
    global emp_counter
    
    db_writer = open('./home/db.txt','a+')
    
    new_data = str(emp_counter) + ',' + new_emp['name'] + ',' + new_emp['city'] + '\n'
    db_writer.write(new_data)
    emp_counter += 1
    
    # Update emp_count file
    with open('./home/emp_count.txt','w') as emp_count:
        emp_count.write(str(emp_counter))
    
    db_writer.close()
    return {'employeeId':str(emp_counter-1)}, 201

# Get all Employee details
@app.route('/employees/all', methods=['GET'])
def get_all_employees():
    db_reader = open('./home/db.txt')
    all_data = db_reader.readlines()
    out_data = []
    
    for line in all_data:
        line = line.strip('\n').split(',')
        emp = {}
        emp['employeeId'], emp['name'], emp['city'] = line
        out_data.append(emp)
        
    db_reader.close()

    return out_data, 200


def binary_search_emp(id, all_data):

    emp = {}
    
    # Binary Search
    low, high = 0, len(all_data) - 1
    mid = None
    
    while low<=high:
        mid = low + (high-low)//2
        mid_line = all_data[mid].strip('\n').split(',')
        
        if mid_line[0] == id:
            emp['employeeId'], emp['name'], emp['city'] = mid_line
            break
        
        
        elif int(mid_line[0]) < int(id):
            low = mid+1
        
        else:
            high = mid-1
            
    return emp,mid
    

# Get Employee details
@app.route('/employee/<id>', methods=['GET'])
def get_employee(id):
    db_reader = open('./home/db.txt')
    all_data = db_reader.readlines()
    db_reader.close()
    
    emp, index = binary_search_emp(id, all_data)
        
    if emp == {}:
        return { 'message' : "Employee with {} was not found".format(id) }, 404
        
    return emp, 200

# Update Employee
@app.route('/employee/<id>', methods=['PUT'])
def update_employee(id):
    new_emp = json.loads(request.data)
    
    db_reader = open('./home/db.txt')
    all_data = db_reader.readlines()
    db_reader.close()
    
    emp, index = binary_search_emp(id, all_data)
    
    if emp == {}:
        return { "message" : "Employee with {} was not found".format(id) }, 404 
    
    emp['name'], emp['city'] = new_emp['name'], new_emp['city']
    
    print(all_data[index])
    print(type(all_data[index]))
    
    all_data[index] = emp['employeeId'] + ',' + new_emp['name'] + ',' + new_emp['city'] + '\n'
    
    with open('./home/db.txt','w') as db_writer:
        db_writer.writelines(all_data)
        
    return emp, 201

# Delete Employee
@app.route('/employee/<id>', methods=['DELETE'])
def delete_employee(id):

    db_reader = open('./home/db.txt')
    all_data = db_reader.readlines()
    db_reader.close()    
    
    emp, index = binary_search_emp(id, all_data)   
    
    if emp == {}:
        return { "message" : "Employee with {} was not found".format(id) }, 404 
    
    all_data.pop(index)
    
    with open('./home/db.txt','w') as db_writer:
        db_writer.writelines(all_data)

    return emp, 200


def search_wrapper(fName, e, n):
    def filter_fun(emp):
        fieldName = fName
        eq = e
        neq = n
        
        if eq is not None:
            if emp[fieldName] == eq:
                return True
            return False

        if neq is not None:
            if emp[fieldName] != neq:
                return True
            return False
    return filter_fun



# Search for employees
@app.route('/employees/search', methods=['POST'])
def search_employees():
    search = json.loads(request.data)
    error = {"messages" : []}
    
    fields = search.get('fields')
    if fields is None or len(fields) == 0:
        return {"messages": ["At least one search criteria should be passed."]}, 400
        
        
    condition = search.get('condition',"AND")
    matched_emps = []
    matched_emp_ids = []
    search_filters = []
        
    
    # Creating list of search filters
    for field in search.get('fields'):
        
        
        fieldName = field.get('fieldName')
        eq = field.get('eq')
        neq = field.get('neq')
        
        
        if fieldName is None:
            error['messages'].append("fieldName must be set.")
            
        elif (eq is None) and (neq is None):
            error['messages'].append("{}: At least one of eq, neq must be set.".format(fieldName))
            
        else:
            filter_fun = search_wrapper(fieldName, eq, neq)
            search_filters.append(filter_fun)
            
    
    #Check if any errors
    if len(error['messages']) != 0:
        return error, 400
        
    
    # Checking each employee
    db_reader = open('./home/db.txt')
    
    for line in db_reader.readlines():
        emp = {}
        emp['employeeId'], emp['name'], emp['city'] = line.strip('\n').split(',')
        
        if int(emp['employeeId']) not in matched_emp_ids:

            
            if condition == "AND":
                accepted = True
                for fun in search_filters:
                    accepted = accepted and fun(emp)
                    
            else:
                accepted = False
                for fun in search_filters:
                    accepted = accepted or fun(emp)
                    
            if accepted:
                matched_emps.append(emp)
                matched_emp_ids.append(int(emp['employeeId']))
                
    db_reader.close()
    return matched_emps, 200
        


if __name__ == '__main__':
    app.run(port=8080,host='0.0.0.0')