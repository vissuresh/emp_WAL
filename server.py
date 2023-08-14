from flask import Flask, request
import json, os
from threading import Thread

# In memory hash_map
with open('./home/data.json') as db:
    memstore = json.load(db)
    emp_counter, log_pointer = int(memstore["metadata"]["emp_counter"]), int(memstore["metadata"]["log_pointer"])
    
    
# number of unflushed changes to disk in log
flush_length = 0

# TO APPEND TO LOG FILE
log_file = open('./home/wal.log','a+')
log_file.seek(0)
next_req_id = len(log_file.readlines())-1

    
# To read n lines, from log_pointer
def goto_line(f, n):
    for i in range(n+1):
        f.readline()
    return f


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


def flush_to_disk():
    global emp_counter, next_req_id, flush_length
    
    memstore["metadata"]["emp_counter"], memstore["metadata"]["log_pointer"] = emp_counter, next_req_id
    
    with open('./home/data.json','w') as db_writer:
        json.dump(memstore, db_writer, indent=4)

    flush_length = 0
    

def log_flush(**kwargs):
    req_id = str(kwargs.get('req_id'))
    method = kwargs.get('method')
    payload = json.dumps(kwargs.get('payload'))
    payload_length = str(len(payload))
    
    log_line = req_id + '|' + method + '|' + payload_length + '|' + payload + '\n'
    
    log_file.write(log_line)
    log_file.flush()
    os.fsync(log_file.fileno())
    
    
    
# ///////////////////////////////////////////
# REPLYAING PENDING ACTIONS ON SERVER RESTART
# ///////////////////////////////////////////

with open("./home/wal.log") as log_reader:
    log_reader = goto_line(log_reader, log_pointer)

    # Line in log: ReqID | Method | Length | Payload
    log_line = log_reader.readline()
    while(log_line):
        req_id, method, length, payload = log_line.split("|")
        payload = json.loads(payload)
        
        if method == "POST":
            memstore["employees"][str(emp_counter)] = payload
            emp_counter +=1
               
        elif method == "PUT":
            memstore["employees"][payload['employeeId']] = {"name":payload["name"], "city":payload["city"]}
            
        elif method == "DELETE":
            memstore["employees"].pop(payload["employeeId"])       
                
        log_line = log_reader.readline()
        
    flush_to_disk()

# //////////////////////////////
# MEMSTORE AND DATA.JSON UPDATED
# //////////////////////////////
        
    
 

app = Flask(__name__)

# Greeting 
@app.route("/greeting", methods=['GET'])
def greeting():
    return 'Hello world!'   

# Create Employee
@app.route('/employee', methods=['POST'])
def create_employee():
    global emp_counter, next_req_id, flush_length
    
    payload = json.loads(request.data)
    memstore["employees"][str(emp_counter)] = payload
    
    log_flush(req_id = next_req_id, method = request.method, payload = payload)
    
    output = {"employeeId":str(emp_counter)}
    
    emp_counter +=1
    flush_length +=1
    next_req_id +=1
    
    if flush_length >= 5:
        flush_to_disk()
    
    return output, 201


# Get all Employee details
@app.route('/employees/all', methods=['GET'])
def get_all_employees():
    employee_list = []
    for e_id, v in memstore["employees"].items():
        v.update({"employeeId":e_id})
        employee_list.append(v)
    
    return employee_list,200


# Get Employee details
@app.route('/employee/<id>', methods=['GET'])
def get_employee(id):
    emp = memstore["employees"].get(id, None)

    if emp is not None:
        return emp,200
    return { 'message' : "Employee with {} was not found".format(id) }, 404


# Update Employee
@app.route('/employee/<id>', methods=['PUT'])
def update_employee(id):
    global next_req_id, flush_length
    
    if memstore["employees"].get(id, None) is None:
        return { 'message' : "Employee with {} was not found".format(id) }, 404
    
    payload = json.loads(request.data)
    memstore["employees"][id] = payload
    
    payload["employeeId"] = id
    
    log_flush(req_id=next_req_id, method=request.method, payload=payload)
    
    flush_length +=1
    next_req_id +=1
    
    if flush_length >= 5:
        flush_to_disk()
    
    return payload, 201


# Delete Employee
@app.route('/employee/<id>', methods=['DELETE'])
def delete_employee(id):
    global next_req_id, flush_length
    
    emp = memstore["employees"].pop(id, None)
    if emp is None:
        return { 'message' : "Employee with {} was not found".format(id) }, 404
    
    emp["employeeId"] = id
    
    payload = {"employeeId":id}
    
    log_flush(req_id=next_req_id, method=request.method, payload=payload)
    
    flush_length +=1
    next_req_id +=1
    
    if flush_length >= 5:
        flush_to_disk()
    
    return emp,200    


# Search for employees
@app.route('/employees/search', methods=['POST'])
def search_employees():
    search = json.loads(request.data)
    error = {"messages" : []}
    
    fields = search.get('fields')
    if fields is None or len(fields) == 0:
        return {"messages": ["At least one search criteria should be passed."]}, 400
        
        
    condition = search.get('condition',"AND")
    matched_emps = {}
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
    for e_id, e_data in memstore["employees"].items():

        if matched_emps.get(e_id) is None:
            
            if condition == "AND":
                accepted = True
                for fun in search_filters:
                    accepted = accepted and fun(e_data)
                    
            else:
                accepted = False
                for fun in search_filters:
                    accepted = accepted or fun(e_data)
                    
            if accepted:
                e_data["employeeId"] = e_id
                matched_emps[e_id] = e_data
                
    return list(matched_emps.values()), 200

    
 
if __name__ == '__main__':
    app.run(port=8080,host='0.0.0.0')