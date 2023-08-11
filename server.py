from flask import Flask, request
import json

def goto_line(f, n):
    for i in range(n-1):
        f.readline()
    return f

app = Flask(__name__)
with open('./home/emp_count.txt') as emp_count:
    try:    
        emp_counter = int(emp_count.readline().strip('\n'))
    except:
        emp_counter = 0
    
flush_length = 0

# In memory hash_map
with open('./home/data.json') as db:
    memstore = json.load(db)
    
    
# Updating pending actions in LOG
with open('./home/log_pointer.txt') as lp:
    log_pointer = int(lp.read())
    

# Reading the log file from line log_pointer. READ 
with open("./home/wal.log") as log_reader:
    log_reader = goto_line(log_reader, log_pointer)
    

    # Line in log: ReqID | Method | Length | Payload
    log_line = log_reader.readline()
    while(log_line):
        print(log_line)
        req_id, method, length, payload = log_line.split("|")
        payload = json.loads(payload)
        
        if method == "POST":
            memstore[emp_counter] = payload
            emp_counter +=1
               
        elif method == "PUT":
            memstore[payload['employeeId']] = {"name":payload["name"], "city":payload["city"]}
            
        elif method == "DELETE":
            memstore.pop(payload["employeeId"])       
            
            
        flush_length +=1
        
        # Write to file storage if flush_length >= 10
        # if flush_length >= 10:
            
        with open('./home/data.json','w') as db_writer:
            json.dump(memstore, db_writer)
            
        with open('./home/emp_count.txt','w') as empCount_writer:
            empCount_writer.write(str(emp_counter))
            
        with open('./home/log_pointer.txt','w') as lp:
            lp.write(req_id+1)
            
        flush_length = 0
            
        log_line = log_reader.readline()
            
    
 


# Greeting 
@app.route("/greeting", methods=['GET'])
def greeting():
    return 'Hello world!'   

# Create Employee
@app.route('/employee', methods=['POST'])
def create_employee():
    pass


# Get all Employee details
@app.route('/employees/all', methods=['GET'])
def get_all_employees():
    pass


# Get Employee details
@app.route('/employee/<id>', methods=['GET'])
def get_employee(id):
    pass


# Update Employee
@app.route('/employee/<id>', methods=['PUT'])
def update_employee(id):
    pass


# Delete Employee
@app.route('/employee/<id>', methods=['DELETE'])
def delete_employee(id):
    pass




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
    pass
    
 
# if __name__ == '__main__':
#     app.run(port=8080,host='0.0.0.0')