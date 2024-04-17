from flask import Flask, render_template, request, redirect, session, jsonify
from flask import request
import mysql.connector
import random
import string
import stripe
from decimal import Decimal
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import make_response
import time
import random
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

stripe.api_key = "sk_test_51O3tLySCEMCjGc1MrH5X3RsLH4DOjz34a0cJvJJXsUT2hCdqi9kmcAQii39f5lTPd1qU8M6GxDs3ugvYKr6plwXH00IOVWbtNj"
def register_intra_routes(app,cursor,db):
  
  @app.route('/deposit', methods=['POST'])
  def deposit():
    try:
        deposit_amount = int(request.form['deposit_amount'])
        print(deposit_amount)
        # Check if the deposit_amount is positive
        if deposit_amount > 0:
            cursor = db.cursor()
            cursor.execute(f"update main_account_balance set balance=balance+{deposit_amount};")
            db.commit()

            return jsonify({'message': "Amount deposited successfully"})
        else:
            return jsonify({'message': "Deposit amount should be positive"})

    except Exception as e:
        return jsonify({'message': str(e)})


  @app.route('/withdraw', methods=['POST'])
  def withdraw():
    try:
        withdraw_amount = int(request.form['withdraw_amount'])
        # Check if the withdraw_amount is positive and doesn't exceed the current balance
        if withdraw_amount > 0:
            cursor = db.cursor()
            cursor.execute("SELECT balance from main_account_balance;")
            current_balance = cursor.fetchone()[0]
            print(current_balance)
            if withdraw_amount <= current_balance:
                cursor = db.cursor()
                cursor.execute(f"update main_account_balance set balance=balance-{withdraw_amount};")
                db.commit()

                return jsonify({'message': "Amount Withdrawn successfully"})
            else:
                return jsonify({'message': "Withdrawal amount exceeds the current balance."})
        else:
            return jsonify({'message': "Withdrawal amount should be positive"})

    except Exception as e:
        return str(e)


  @app.route('/download-receipt/<string:bill_no>')
  def download_receipt(bill_no):
    try:
        cursor = db.cursor()

        # Fetch data from the `customer_pays_bill` table
        cursor.execute("SELECT time_of_payment, total_cost FROM customer_pays_bill WHERE bill_no = %s", (bill_no,))
        result = cursor.fetchone()

        if result:
            time_of_payment, total_cost = result

            # Fetch the customer's full name from the `customer` table
            cursor.execute("SELECT full_name FROM customer WHERE username = %s", (session['customer_username'],))
            customer_name = cursor.fetchone()[0]

            # Fetch the order IDs from the `bill` table
            cursor.execute("SELECT order_id FROM bill WHERE bill_no = %s", (bill_no,))
            order_ids = [row[0] for row in cursor.fetchall()]

            # Initialize the order details list
            order_details = []

            # Fetch food, quantity, and cost from the `order1` table for each 
            # order ID
            for order_id in order_ids:
                cursor.execute("SELECT food, quantity, cost FROM order1 WHERE order_id = %s", (order_id,))
                order_details.extend(cursor.fetchall())

            # Generate the PDF receipt using ReportLab
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            # Register the Arial Unicode MS font (replace 'path_to_font_file' with the actual font file path)
            pdfmetrics.registerFont(TTFont('SegoeUI', 'font/segoeui.ttf'))

            # Use the font when creating the canvas
            p.setFont("SegoeUI", 18)  # Use the desired font name and size
            p.drawString(100, 750, f"Bill No: {bill_no}")
            p.drawString(100, 730, f"time_of_payment: {time_of_payment}")
            p.drawString(100, 710, f"Customer Name: {customer_name}")
            y_position = 690  # Starting Y position for order details
            for detail in order_details:
                order_row = f"Food: {detail[0]}, Quantity: {detail[1]}, Cost: ${detail[2]}"
                p.drawString(100, y_position, order_row)
                y_position -= 20  # Adjust the spacing
            p.drawString(100, y_position, f"Total Cost: ${total_cost}")
            p.showPage()
            p.save()
            buffer.seek(0)

            # Create a response and set appropriate headers
            response = make_response(buffer.read())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=receipt_{bill_no}.pdf'
            return response
        else:
            return "Receipt not found", 404
    except Exception as e:
        return str(e), 500

  @app.route('/process-payment', methods=['POST','GET'])
  def process_payment():
    try:
        payment_method_id = request.form['paymentMethodId']
        total_cost = request.form['total_cost']
        bill_no = request.form['bill_no']
        print(total_cost)
        cur = db.cursor()
        cur.execute(f"update main_account_balance set balance=balance+{total_cost};")
        cur = db.cursor()
        # Use placeholders and pass values as parameters to avoid SQL injection
        cur.execute(f"INSERT INTO customer_pays_bill (customer_username, bill_no, total_cost, time_of_payment) VALUES('{session['customer_username']}','{bill_no}',{total_cost},now());")
        # insert_query = "INSERT INTO customer_pays_bill (customer_username, bill_no, total_cost) VALUES (%s, %s, %d)"

        # # Execute the query with the parameters
        # cur.execute(insert_query, (session['customer_username'], bill_no, total_cost))
        db.commit()


        # Rest of your payment processing logic, where you can use `total_cost` and `bill_no`.

        # Create a PaymentIntent to confirm the payment
        intent = stripe.PaymentIntent.create(
            amount=total_cost,
            currency='usd',
            payment_method=payment_method_id,
            confirmation_method='manual',
            confirm=True,
            return_url='/payment-success'
        )

        # Handle the payment success and return a response to the client
        return jsonify({'clientSecret': intent.client_secret})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)})


# Define a route for displaying a success message
  @app.route('/payment-success')
  def payment_success():
    return render_template('payment_success.html')

  @app.route('/checkout', methods=['POST'])
  def checkout():
    # Payment form data
    token = request.form['stripeToken']
    amount = 1000  # $10.00 in cents

    try:
        # Create a charge using the test card and amount
        charge = stripe.Charge.create(
            amount=amount,
            currency='rs',
            source=token,
            description='Test Charge'
        )
        return render_template('success.html', charge=charge)
    except stripe.error.CardError as e:
        # Display payment failure
        return render_template('failure.html', error=e)

  @app.route('/pay-amount', methods=['POST'])
  def pay_amount():
    if request.method == 'POST':
        data = request.get_json()
        total_amount = data.get('total_amount')

        # Perform the payment process here
        # Update the payment status in the database

        # Return a response (you can customize it based on your application logic)
        return jsonify({'status': 'success'})  # Payment successful

  @app.route('/view-receipts')
  def view_receipts():
    if 'customer_username' in session:
        cursor = db.cursor()
        cursor.execute("""
        SELECT bill_no, total_cost
        FROM customer_pays_bill
        WHERE customer_username = %s;
        """, (session['customer_username'],))
        
        # Fetch all the rows
        receipts = cursor.fetchall()
        user_details = get_user_details(session['customer_username'])
        return render_template('view-receipts.html', receipts=receipts,user_details=user_details)
    else:
        return redirect('/customer-login')


# Function to get unpaid bill details
  def get_unpaid_bill_from_bill_table(customer_username):

    #just check if there is bill_no in bill table,which is not in customer_pays_bill table, and the order_id of that bill_no from bill table , is in place_order table where customer_username is session's customer_username
    query = """
        SELECT b.bill_no as total_cost
        FROM bill as b
        JOIN place_order as po ON b.order_id = po.order_id
        JOIN order1 as o1 ON po.order_id = o1.order_id
        LEFT JOIN customer_pays_bill as cpb ON b.bill_no = cpb.bill_no
        WHERE po.customer_username = %s
        AND cpb.bill_no IS NULL
        GROUP BY b.bill_no
    """

    cursor.execute(query, (customer_username,))
    result = cursor.fetchall()

    if result:
        return result[0]  # Assuming there is only one unpaid bill for a customer
    else:
        return None



# Function to get order_ids for a customer
  def get_order_ids_for_customer(customer_username):
    # here check the chef_undertakes_order -> order_id, then search those order_id in place_order table , those which have customer_username as session['customer_username'] will go in answer, and those order_id should not be associated with a bill_no, get it from bill table, which is there in customer_pays_bill table
    # Query to get order_ids for a customer:
    query = """
        SELECT cuo.order_id
        FROM chef_undertakes_order as cuo
        JOIN place_order as po ON cuo.order_id = po.order_id
        LEFT JOIN bill as b ON cuo.order_id = b.order_id
        LEFT JOIN customer_pays_bill as cpb ON b.bill_no = cpb.bill_no
        WHERE po.customer_username = %s
        AND cpb.bill_no IS NULL

    """

    cursor.execute(query, (customer_username,))
    results = cursor.fetchall()

    # Extract the order_ids from the results
    order_ids = [result[0] for result in results]

    return order_ids  

# Function to insert bill details
  def insert_bill_details(bill_no, order_ids):
    cursor = db.cursor()

    # Create a set to store the unique order_ids
    unique_order_ids = set()

    # Check if the order_id is not already present in the bill table
    for order_id in order_ids:
        query = "SELECT 1 FROM bill WHERE order_id = %s LIMIT 1"
        cursor.execute(query, (order_id,))
        if cursor.fetchone() is None:
            unique_order_ids.add(order_id)

    # Insert unique order_ids into the bill table
    query = "INSERT INTO bill (bill_no, order_id) VALUES (%s, %s)"
    for order_id in unique_order_ids:
        cursor.execute(query, (bill_no, order_id))

    # Commit the changes to the database
    db.commit()

    
# Function to calculate the total cost of a bill
  def calculate_total_cost(bill_no):
    # for this bill_no, sum the cost of all order_id associated with it , get cost of order_id from place_order table
    query = """
        SELECT SUM(po.total_cost)
        FROM place_order as po
        JOIN bill as b ON po.order_id = b.order_id
        WHERE b.bill_no = %s
    """

    cursor.execute(query, (bill_no,))
    result = cursor.fetchone()

    if result and result[0]:
        total_cost = result[0]
    else:
        total_cost = 0

    return total_cost

  @app.route('/view-bill')
  def view_bill():
    if 'customer_username' in session:
        user_details = get_user_details(session['customer_username'])

        # Check if there's an unpaid bill associated with the customer
        result = get_unpaid_bill_from_bill_table(session['customer_username'])

        if result:
            bill_no= result[0]
        else:
            # If there's no unpaid bill, generate a new unique bill number and insert it into the database
            bill_no = generate_unique_billno()
            
        # Now insert the bill number and order_ids into the bill table
        order_ids = get_order_ids_for_customer(session['customer_username'])
        print("*********Order id",order_ids)
        if order_ids:
            insert_bill_details(bill_no, order_ids)
        else:
            return render_template('view-bill.html', bill_no=None, total_cost=0, user_details=user_details)

        # Calculate the total cost for the bill
        print("*************Bill no",bill_no)
        total_cost = calculate_total_cost(bill_no)

        # Render the view-bill template with the bill details
        return render_template('view-bill.html', bill_no=bill_no, total_cost=total_cost, user_details=user_details)
    else:
        return redirect('/customer-login')
    

  @app.route('/serve-food/<string:orderId>', methods=['GET','POST'])
  def serve_food(orderId):
    cur=db.cursor()
    cur.execute(f"insert into served values('{orderId}');")
    db.commit()
    return jsonify({'status': 'success'})
  
    
  @app.route('/waiter-serves')
  def waiter_serves():
    if 'waiter_username' in session:
        waiter_details = get_waiter_details(session['waiter_username'])

        # Step 1: Fetch order_id values from waiter_accepts_call table
        cursor = db.cursor()
        query = "SELECT order_id FROM waiter_accepts_call WHERE waiter_username = %s"
        cursor.execute(query, (session['waiter_username'],))
        order_ids = [row[0] for row in cursor.fetchall()]

        serve_details = []

        # Step 2: Retrieve table_no and customer_username for each order_id
        for order_id in order_ids:
            query = "SELECT tableno, customer_username FROM place_order WHERE order_id = %s"
            cursor.execute(query, (order_id,))
            result = cursor.fetchone()

            if result:
                table_no, customer_username = result
                print(customer_username)
                # Step 3: Retrieve full_name of the customer
                query = "SELECT full_name FROM customer WHERE username = %s"
                cursor.execute(query, (customer_username,))
                full_name = cursor.fetchone()[0]
                print(full_name)

                serve_details.append({
                    "order_id": order_id,
                    "table_no": table_no,
                    "full_name": full_name
                })

        return render_template('waiter-serves.html', serve_details=serve_details, waiter_details=waiter_details)
    else:
        return redirect('/waiter-login')




  @app.route('/check-waiter-called/<string:orderId>', methods=['GET','POST'])
  def check_waiter_called(orderId):
    cursor = db.cursor()
    query = "SELECT * FROM chef_calls WHERE order_id = %s"
    cursor.execute(query, (orderId,))
    result = cursor.fetchone()
    #mycursor.close()

    if result:
        return jsonify({'isCalled': True})
    else:
        return jsonify({'isCalled': False})

  @app.route('/accept-call/<string:orderId>', methods=['POST', 'GET'])
  def accept_call(orderId):
    if 'waiter_username' in session:
        waiter_username = session['waiter_username']

        # Insert the waiter's username and order ID into the waiter_accepts_call table
        cursor = db.cursor()
        insert_query = "INSERT INTO waiter_accepts_call (waiter_username, order_id) VALUES (%s, %s)"
        try:
            cursor.execute(insert_query, (waiter_username, orderId))
            db.commit()
            #mycursor.close()
            return jsonify({'status': 'success', 'message': 'Call accepted successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Failed to accept the call: ' + str(e)})
    else:
        return jsonify({'status': 'error', 'message': 'Waiter is not logged in'})


  @app.route('/view-calls')
  def view_calls():
    if 'waiter_username' in session:
        # Fetch order details for the logged-in user from the database
        cur = db.cursor()
        cur.execute("SELECT * from chef_calls;")
        call_details = cur.fetchall()
        cur = db.cursor()
        cur.execute("SELECT * FROM waiter_accepts_call;")
        waiter_accepts_call = cur.fetchall()
        cur.close()
        waiter_details = get_waiter_details(session['waiter_username'])
        # Filter the order_details based on your conditions
        filtered_orders = []
        for call in call_details:
            order_id = call[1]
            should_display = False
            should_display1 = True
            for accepted_call in waiter_accepts_call:
                if order_id == accepted_call[1]:
                    should_display1 = False
            for accepted_call in waiter_accepts_call:
                if order_id == accepted_call[1] and accepted_call[0] == session['waiter_username']:
                    should_display = True
                    # Delete the record from chef_calls table
                    cur = db.cursor()
                    cur.execute("DELETE FROM chef_calls WHERE order_id = %s;", (order_id,))
                    db.commit()
                    cur.close()

            if should_display1 or should_display:
                filtered_orders.append(call)

        return render_template('view-calls.html', call_details=filtered_orders, waiter_details=waiter_details)
    
    else:
        return redirect('/waiter-dashboard')



  @app.route('/get-serves-by-waiters',methods=['GET'])
  def get_serves_by_waiters():
    try:
        # Connect to the database and create a cursor
        cursor = db.cursor()
        
        # Execute a query to select the data from the chef_undertakes_order table
        cursor.execute("select order_id from served;")
        #cursor.execute("SELECT chef_username, order_id FROM chef_undertakes_order")
        
        # Fetch all the rows from the query result
        serves = cursor.fetchall()
        
        # Close the cursor
        #mycursor.close()
        for row in serves:
            print(row[0])
        # Prepare the data to return as a JSON response
        orders_served = [{'order_id': row[0]} for row in serves]

        # Return the data as a JSON response
        return jsonify({'servedOrders': orders_served})
    except Exception as e:
        # Handle any exceptions or errors that may occur
        return jsonify({'error': 'An error occurred: ' + str(e)})


  @app.route('/get-orders-served-by-waiters',methods=['GET'])
  def get_orders_served_by_waiters():
    try:
        # Connect to the database and create a cursor
        cursor = db.cursor()

        # Execute the SQL query
        query = """
        SELECT s.order_id, w.full_name
        FROM served AS s
        JOIN waiter_accepts_call AS wac ON s.order_id = wac.order_id
        JOIN waiter AS w ON wac.waiter_username = w.username;
        """
        cursor.execute(query)

        # Fetch the results
        result = cursor.fetchall()

        #mycursor.close()
        for row in result:
            print(row[0]," ",row[1])
        # Prepare the data to return as a JSON response
        orders = [{'waiter_name': row[1], 'order_id': row[0]} for row in result]

        # Return the data as a JSON response
        return jsonify({'servedOrders': orders})
    except Exception as e:
        # Handle any exceptions or errors that may occur
        return jsonify({'error': 'An error occurred: ' + str(e)})

  @app.route('/get-calls-accepted-by-waiters', methods=['GET'])
  def get_calls_accepted_by_waiters():
    try:
        # Connect to the database and create a cursor
        cursor = db.cursor()
        
        # Execute a query to select the data from the waiter_accepts_call table
        cursor.execute("SELECT w.full_name, a.order_id FROM waiter w JOIN waiter_accepts_call a ON a.waiter_username=w.username")
        
        # Fetch all the rows from the query result
        accepted_calls = cursor.fetchall()

        # Prepare the data to return as a JSON response
        calls = [{'waiter_name': row[0], 'order_id': row[1]} for row in accepted_calls]

        # Return the data as a JSON response
        return jsonify({'acceptedCalls': calls})
    except Exception as e:
        # Handle any exceptions or errors that may occur
        return jsonify({'error': 'An error occurred: ' + str(e)})


  @app.route('/get-calls-by-chefs',methods=['GET'])
  def get_calls_by_chefs():
    try:
        # Connect to the database and create a cursor
        cursor = db.cursor()
        
        # Execute a query to select the data from the chef_undertakes_order table
        cursor.execute("select order_id from chef_calls")
        #cursor.execute("SELECT chef_username, order_id FROM chef_undertakes_order")
        
        # Fetch all the rows from the query result
        calls = cursor.fetchall()
        print("**************",calls)
        
        # Close the cursor
        #mycursor.close()
        for row in calls:
            print(row[0])
        # Prepare the data to return as a JSON response
        orders = [{'order_id': row[0]} for row in calls]
        print(orders)
        # Return the data as a JSON response
        return jsonify({'calls': orders})
    except Exception as e:
        # Handle any exceptions or errors that may occur
        return jsonify({'error': 'An error occurred: ' + str(e)})


  @app.route('/get-orders-undertaken-by-chefs',methods=['GET'])
  def get_orders_undertaken_by_chefs():
    try:
        # Connect to the database and create a cursor
        cursor = db.cursor()
        
        # Execute a query to select the data from the chef_undertakes_order table
        # cursor.execute("select c.full_name, u.order_id from chef_undertakes_order u join chef c on c.username=u.chef_username ;")
        cursor.execute("SELECT chef_username, order_id FROM chef_undertakes_order")
        
        # Fetch all the rows from the query result
        undertaken_orders = cursor.fetchall()
        
        # Close the cursor
        #mycursor.close()
        for row in undertaken_orders:
            print(row[0]," ",row[1])
        # Prepare the data to return as a JSON response
        orders = [{'chef_name': row[0], 'order_id': row[1]} for row in undertaken_orders]

        # Return the data as a JSON response
        return jsonify({'undertakenOrders': orders})
    except Exception as e:
        # Handle any exceptions or errors that may occur
        return jsonify({'error': 'An error occurred: ' + str(e)})

  def generate_unique_billno():
    while True:
        # Generate a random alphanumeric order ID (e.g., "ab12")
        alphanumeric_chars = string.ascii_letters + string.digits
        bill_no = ''.join(random.choice(alphanumeric_chars) for _ in range(4))
        
        # Check if the generated order ID is unique
        cursor = db.cursor()
        check_query = "SELECT bill_no FROM bill;"
        cursor.execute(check_query)
        data = cursor.fetchall()
        flag=0
        for item in data:
            t_bill = item[0]
            if t_bill==bill_no:
                flag=1
        #mycursor.close()
        
        if not flag:
            # The generated order ID is unique; return it
            return bill_no

  @app.route('/undertake-order/<string:orderId>', methods=['POST','GET'])
  def undertake_order(orderId):
    if 'chef_username' in session:
        chef_username = session['chef_username']
        # Insert the chef's username and order ID into the chef_views_order table
        cursor = db.cursor()
        insert_query = "INSERT INTO chef_undertakes_order (chef_username, order_id) VALUES (%s, %s)"
        try:
            cursor.execute(insert_query, (chef_username, orderId))
            
            db.commit()
            #mycursor.close()
            return jsonify({'status': 'success', 'message': 'Order undertaken successfully'})
        except Exception as e:
            return jsonify({'status': 'success', 'message': 'Order undertaken successfully: ' + str(e)})
    else:
        return jsonify({'status': 'error', 'message': 'Chef is not logged in'})
    
  @app.route('/call-waiter/<string:orderId>', methods=['POST','GET'])
  def call_waiter(orderId):
    if 'chef_username' in session:
        chef_username = session['chef_username']

        # Insert the chef's username and order ID into the chef_views_order table
        cursor = db.cursor()
        insert_query = "INSERT INTO chef_calls (kitchen_no,order_id) VALUES ((SELECT kitchen_no FROM chef WHERE username=%s),%s)"
        try:
            cursor.execute(insert_query, (chef_username,orderId))
            db.commit()
            #mycursor.close()
            return jsonify({'status': 'success', 'message': 'Waiter called successfully'})
        except Exception as e:
            return jsonify({'status': 'success', 'message': 'Failed to call the waiter: ' + str(e)})
    else:
        return jsonify({'status': 'error', 'message': 'Chef is not logged in'})

  @app.route('/cancel-order/<string:order_id>', methods=['POST','GET'])
  def cancel_order(order_id):
    cur = db.cursor()
    cur.execute(f"delete from place_order where order_id = %s;", (order_id,))
    cur.execute(f"delete from order1 where order_id = %s;", (order_id,))
    db.commit()
    cur.close()

    # Return a success response
    return jsonify({'status': 'success', 'message': 'Order canceled successfully'})



  @app.route('/get-order-detail/<orderId>', methods=['GET'])
  def get_order_detail(orderId):
    try:
        # Use a context manager to handle the cursor
        with db.cursor() as cursor:
            # Query the database for all rows with the specified orderId
            cursor.execute("SELECT food, quantity, cost FROM order1 WHERE order_id = %s", (orderId,))
            order_data = cursor.fetchall()
            #print("-------------------", order_data)

        if order_data:
            # If data was found, return it as a list of dictionaries in a JSON response
            result = []
            for row in order_data:
                food, quantity, cost = row
                result.append({'food': food, 'quantity': quantity, 'cost': cost})
            return jsonify(result)
        else:
            # If no rows are found, return an error message
            return jsonify({'error': 'Order not found'})
    except Exception as e:
        return jsonify({'error': 'An error occurred: ' + str(e)})


  @app.route('/view-account-balance')
  def view_account_balance():
    if 'cashier_username' in session:
        # Fetch order details for the logged-in user from the database
        cursor = db.cursor()
        cursor.execute("select balance from main_account_balance;")
        balance=cursor.fetchone()[0]
        cashier_details = get_cashier_details(session['cashier_username'])
        #mycursor.close()

        return render_template('view-account-balance.html', balance=balance,cashier_details=cashier_details)
    else:
        return redirect('/cashier-login')

  @app.route('/view-order')
  def view_order():
    if 'customer_username' in session:
        # Fetch order details for the logged-in user from the database
        cursor = db.cursor()
        cursor.execute("SELECT order_id, total_cost FROM place_order WHERE customer_username = %s", (session['customer_username'],))
        order_details = cursor.fetchall()
        print(order_details)
        user_details = get_user_details(session['customer_username'])
        #mycursor.close()

        return render_template('view-order.html', order_details=order_details,user_details=user_details)
    else:
        return redirect('/customer-login')



  @app.route('/check-awaiting-order')
  def check_awaiting_order():
    if 'chef_username' in session:
        # Fetch order details for the logged-in user from the database
        cur = db.cursor()
        cur.execute("SELECT order_id, total_cost FROM place_order;")
        order_details = cur.fetchall()

        cur.execute("SELECT * FROM chef_undertakes_order;")
        chef_undertakes_order = cur.fetchall()

        user_details = get_chef_details(session['chef_username'])
        cur.close()

        # Filter the order_details based on your conditions
        filtered_orders = []
        for order in order_details:
            order_id = order[0]
            should_display = False
            should_display1 = True

            for undertake_order in chef_undertakes_order:
                if order_id == undertake_order[1]:
                    should_display1 = False

            for undertake_order in chef_undertakes_order:
                if order_id == undertake_order[1] and undertake_order[0] == session['chef_username']:
                    should_display = True

            if should_display1 or should_display:
                filtered_orders.append(order)

        return render_template('check_awaiting_order.html', order_details=filtered_orders, user_details=user_details)
    else:
        return redirect('/chef-dashboard')

  @app.route('/sign-out')
  def sign_out():
    # Clear the session to sign the user out
    session.pop('customer_username', None)
    return redirect('/')

  @app.route('/chef-sign-out')
  def chef_sign_out():
    # Clear the session to sign the user out
    session.pop('chef_username', None)
    return redirect('/')

  @app.route('/waiter-sign-out')
  def waiter_sign_out():
    # Clear the session to sign the user out
    session.pop('waiter_username', None)
    return redirect('/')

  @app.route('/cashier-sign-out')
  def cashier_sign_out():
    # Clear the session to sign the user out
    session.pop('cashier_username', None)
    return redirect('/')


  @app.route('/order-food')
  def order_food():
    if 'customer_username' in session:
        # Fetch order details for the logged-in user from the database
        user_details = get_user_details(session['customer_username'])
        #mycursor.close()

        return render_template('order-food.html',user_details=user_details)
    else:
        return redirect('/customer-login')



  def generate_order_id():
    cursor = db.cursor()
    select_query = "SELECT order_id FROM order1 ORDER BY order_id DESC LIMIT 1"
    cursor.execute(select_query)
    last_order_id = cursor.fetchone()
    cursor.close()

    if last_order_id:
        new_order_id = last_order_id[0] + 56
    else:
        # If there are no existing orders, start from 1
        new_order_id = 1

    return new_order_id
    



  def insert_order_details(order_id, order_data, tableno):
    try:
        cursor = db.cursor()

        # Loop through the order_data and insert each item into the order table
        for item in order_data:
            food = item['food']
            quantity = item['quantity']
            cost = item['total']

            # Insert the order details into the 'order' table
            insert_order_query = "INSERT INTO `order1` (order_id, food, quantity, cost) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_order_query, (order_id, food, quantity, cost))

        # Commit the changes to the database
        db.commit()
        #mycursor.close()
        total_cost = 0  # Initialize the total cost for the order

        # Loop through the form fields to gather order items and quantities
        for item in order_data:
            total_cost += item['total']

        # Insert the order ID, customer username, and total cost into the 'place_order' table
        cursor = db.cursor()
        insert_places_query = "INSERT INTO place_order (customer_username, order_id, total_cost, tableno) VALUES (%s, %s, %s,%s)"
        cursor.execute(insert_places_query, (session['customer_username'], order_id, total_cost, tableno))
        db.commit()
        #mycursor.close()

        return True  # Return success
    except Exception as e:
        # Handle any exceptions or errors
        print("Error:", str(e))
        return False  # Return failure

# In your Flask route, call this function to insert the order details into the database
  @app.route('/process-order', methods=['POST'])
  def process_order():
    try:
        order_data = request.json.get('orderData')
        tableno = request.json.get('tableno')

        # Insert order details into the 'order' table
        if insert_order_details(generate_order_id(), order_data, tableno):
            # If the insertion was successful, you can return a success message
            return jsonify({"status": "success"})
        else:
            # If there was an error, return an error message
            return jsonify({"status": "error", "message": "Failed to insert order details into the database"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

  @app.route('/place-order', methods=['POST'])
  def place_order():
    if 'customer_username' in session:
        # Retrieve order details from the JSON data
        order_data = request.json.get('orderData')
        tableno = request.json.get('tableno')
        
        # Calculate total cost
        total_cost = sum(item['total'] for item in order_data)
        
        order_id = generate_order_id()
        cursor = db.cursor()

        # Insert the order ID, customer username, total cost, and table number into the 'place_order' table
        insert_places_query = "INSERT INTO place_order (customer_username, order_id, total_cost, tableno) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_places_query, (session['customer_username'], order_id, total_cost, tableno))
        db.commit()
        cursor.close()

        return "Order placed successfully!"

    else:
        return redirect('/customer-login')

  @app.route('/pay-bill')
  def pay_bill():
    if 'customer_username' in session:
        # Implement code to display and pay bills
        # You can retrieve and display bills for the logged-in customer
        # and handle payment logic here
        return "Pay bill page"

    else:
        return redirect('/customer-login')

# Modify the login route

  def get_chef_details(user_id):
    cursor = db.cursor()
    cursor.execute("SELECT full_name, mobile_number, kitchen_no, address FROM chef WHERE username = %s", (user_id,))
    user_details = cursor.fetchone()
    #mycursor.close()
    return user_details 

  def get_cashier_details(user_id):
    cursor = db.cursor()
    cursor.execute("SELECT full_name, mobile_number, address FROM cashier WHERE username = %s", (user_id,))
    cashier_details = cursor.fetchone()
    #mycursor.close()
    return cashier_details

  def get_user_details(user_id):
    cursor = db.cursor()
    cursor.execute("SELECT full_name, mobile_number, address FROM customer WHERE username = %s", (user_id,))
    user_details = cursor.fetchone()
    #mycursor.close()
    return user_details
# The customer dashboard route does not need the user_id in the URL

  def get_waiter_details(waiter_id):
    cursor = db.cursor()
    cursor.execute("SELECT full_name, mobile_number, address FROM waiter WHERE username = %s", (waiter_id,))
    waiter_details = cursor.fetchone()
    cursor.close()
    return waiter_details
# The customer dashboard route does not need the user_id in the URL

  @app.route('/customer-dashboard')
  def customer_dashboard():
    if 'customer_username' in session:
        # The user is logged in, display the customer dashboard
        user_details = get_user_details(session['customer_username'])  # Fetch user details based on the session's customer username
        return render_template('customer-dashboard.html', user_details=user_details)
    else:
        return redirect('/customer-login')
    
  @app.route('/cashier-dashboard')
  def cashier_dashboard():
    if 'cashier_username' in session:
        # The user is logged in, display the customer dashboard
        cashier_details = get_cashier_details(session['cashier_username'])  # Fetch user details based on the session's cashier username
        return render_template('cashier-dashboard.html', cashier_details=cashier_details)
    else:
        return redirect('/waiter-login')
    
  @app.route('/waiter-dashboard')
  def waiter_dashboard():
    if 'waiter_username' in session:
        # The user is logged in, display the customer dashboard
        waiter_details = get_waiter_details(session['waiter_username'])  # Fetch user details based on the session's waiter username
        return render_template('waiter-dashboard.html', waiter_details=waiter_details)
    else:
        return redirect('/waiter-login')


  @app.route('/signup', methods=['POST','GET'])
  def signup():
    new_username = request.form['newUsername']
    new_password = request.form['newPassword']
    mobile_number = request.form['mobileNumber']
    full_name = request.form['fullName']
    address = request.form['address']

    # Insert new customer data into the MySQL database
    cursor = db.cursor()
    insert_query = "INSERT INTO customer (username, password, mobile_number, full_name, address) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(insert_query, (new_username, new_password, mobile_number, full_name, address))
    db.commit()
    #mycursor.close()
    good_message = "You are registered successfully. Now Login"
    return render_template('customer-login.html', good_message=good_message)


  @app.route('/cashier-signup', methods=['POST','GET'])
  def cashier_signup():
    new_username = request.form['newUsername']
    new_password = request.form['newPassword']
    mobile_number = request.form['mobileNumber']
    full_name = request.form['fullName']
    address = request.form['address']

    # Insert new customer data into the MySQL database
    cursor = db.cursor()
    insert_query = "INSERT INTO cashier (username, password, mobile_number, full_name, address) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(insert_query, (new_username, new_password, mobile_number, full_name, address))
    db.commit()
    #mycursor.close()
    good_message = "You are registered successfully. Now Login"
    return render_template('cashier-login.html', good_message=good_message)


  @app.route('/waiter-signup', methods=['POST','GET'])
  def waiter_signup():
    new_username = request.form['newUsername']
    new_password = request.form['newPassword']
    mobile_number = request.form['mobileNumber']
    full_name = request.form['fullName']
    address = request.form['address']

    # Insert new customer data into the MySQL database
    cursor = db.cursor()
    insert_query = "INSERT INTO waiter (username, password, mobile_number, full_name, address) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(insert_query, (new_username, new_password, mobile_number, full_name, address))
    db.commit()
    #mycursor.close()
    good_message = "You are registered successfully. Now Login"
    return render_template('waiter-login.html', good_message=good_message)


  @app.route('/chef-signup', methods=['POST','GET'])
  def chef_signup():
    new_username = request.form['newUsername']
    new_password = request.form['newPassword']
    mobile_number = request.form['mobileNumber']
    full_name = request.form['fullName']
    address = request.form['address']
    kitchen_no = request.form['kitchen_no']

    # Insert new customer data into the MySQL database
    cursor = db.cursor()
    insert_query = "INSERT INTO chef (username, password, mobile_number, full_name, kitchen_no, address) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(insert_query, (new_username, new_password, mobile_number, full_name, kitchen_no, address))
    db.commit()
    #mycursor.close()
    good_message = "You are registered successfully. Now Login"
    return render_template('chef-login.html', good_message=good_message)


  @app.route('/login', methods=['POST'])
  def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Perform customer login and authentication using the 'username'
        cursor = db.cursor()
        select_query = "SELECT username, password FROM customer WHERE username = %s"
        cursor.execute(select_query, (username,))
        customer = cursor.fetchone()
        #mycursor.close()

        if customer:
            if customer[1] == password:
                # Successful login, set the session
                session['customer_username'] = username
                return redirect('/customer-dashboard')
            else:
                error_message = "Invalid credentials. Please try again."
        else:
            error_message = "You are not registered. Sign up Please."

        return render_template('customer-login.html', error_message=error_message)

    return render_template('customer-login.html')

  @app.route('/cashier-login', methods=['GET', 'POST'])
  def cashier_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Perform customer login and authentication using the 'username'
        cursor = db.cursor()
        select_query = "SELECT username, password FROM cashier WHERE username = %s"
        cursor.execute(select_query, (username,))
        cashier = cursor.fetchone()
        #mycursor.close()

        if cashier:
            if cashier[1] == password:
                # Successful login, set the session
                session['cashier_username'] = username
                return redirect('/cashier-dashboard')
            else:
                error_message = "Invalid credentials. Please try again."
        else:
            error_message = "You are not registered. Sign up Please."

        return render_template('cashier-login.html', error_message=error_message)

    return render_template('cashier-login.html')

  @app.route('/waiter-login', methods=['GET', 'POST'])
  def waiter_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Perform customer login and authentication using the 'username'
        cursor = db.cursor()
        select_query = "SELECT username, password FROM waiter WHERE username = %s"
        cursor.execute(select_query, (username,))
        waiter = cursor.fetchone()
        #mycursor.close()

        if waiter:
            if waiter[1] == password:
                # Successful login, set the session
                session['waiter_username'] = username
                return redirect('/waiter-dashboard')
            else:
                error_message = "Invalid credentials. Please try again."
        else:
            error_message = "You are not registered. Sign up Please."

        return render_template('waiter-login.html', error_message=error_message)

    return render_template('waiter-login.html')

  @app.route('/chef-dashboard')
  def chef_dashboard():
    if 'chef_username' in session:
        # The user is logged in, display the user dashboard
        user_details = get_chef_details(session['chef_username'])  # Fetch user details based on the session's customer username
        return render_template('chef-dashboard.html', user_details=user_details)
    else:
        return redirect('/chef-login')

  @app.route('/chef-login', methods=['GET', 'POST'])
  def chef_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Perform customer login and authentication using the 'username'
        cursor = db.cursor()
        select_query = "SELECT username, password FROM chef WHERE username = %s"
        cursor.execute(select_query, (username,))
        chef = cursor.fetchone()
        #mycursor.close()

        if chef:
            if chef[1] == password:
                # Successful login, set the session
                session['chef_username'] = username
                return redirect('/chef-dashboard')
            else:
                error_message = "Invalid credentials. Please try again."
        else:
            error_message = "You are not registered. Please, Sign up."

        return render_template('chef-login.html', error_message=error_message)

    return render_template('chef-login.html')

  @app.route('/')
  def home():
    return render_template('index.html')

  @app.route('/customer-login')
  def customer_login():
    return render_template('customer-login.html')
