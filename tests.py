import unittest
import json
from app import app, get_db_connection, db_query

class GodownTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def login(self, username, password):
        return self.client.post('/api/login', json={
            'username': username,
            'password': password
        })

    def logout(self):
        return self.client.post('/api/logout')

    def test_01_login_success(self):
        """Test successful login and session establishment"""
        res = self.login('head', '123')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode('utf-8'))
        self.assertEqual(data.get('success'), True)

    def test_02_login_failure(self):
        """Test failed login with incorrect credentials"""
        res = self.login('head', 'wrong_password')
        self.assertEqual(res.status_code, 401)

    def test_03_admin_user_endpoint_restricted(self):
        """Verify that user management endpoints are restricted to 'head' role only"""
        # Unauthorized access without login
        res = self.client.get('/api/users')
        self.assertEqual(res.status_code, 403)

        # Login as non-admin role (hostel role)
        self.login('boyshostel', '123')
        res = self.client.get('/api/users')
        self.assertEqual(res.status_code, 403)
        self.logout()

    def test_04_bills_visibility_restriction(self):
        """Verify that bills visibility is restricted: others (hostel) see empty list, clerk/admin/accounts see all"""
        # Login as accounts role
        self.login('accounts', '123')
        res = self.client.get('/api/bills')
        self.assertEqual(res.status_code, 200)
        self.logout()

        # Login as hostel role (boyshostel)
        self.login('boyshostel', '123')
        res = self.client.get('/api/bills')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode('utf-8'))
        self.assertEqual(data, []) # Hostel role receives empty list for privacy
        self.logout()

    def test_05_grocery_master_crud(self):
        """Test Master Grocery items CRUD operations"""
        self.login('head', '123')
        
        # Create a new grocery catalog item
        test_item = {
            'Grocery_Code': 9999,
            'Grocery_Items_Kan': 'ಟೆಸ್ಟ್ ಐಟಂ',
            'Grocery_Items_Eng': 'Test Item',
            'Grocery_Category': 'Grocery',
            'Qtl_Kg_Ltr': 'Kg',
            'Std_Rate': 50.0
        }
        res = self.client.post('/api/grocery-items', json=test_item)
        self.assertEqual(res.status_code, 200)

        # Retrieve catalog item
        res = self.client.get('/api/grocery-items')
        self.assertEqual(res.status_code, 200)
        items = json.loads(res.data.decode('utf-8'))
        item_codes = [r['Grocery_Code'] for r in items]
        self.assertIn(9999, item_codes)

        # Edit catalog item
        edit_data = {
            'Grocery_Items_Kan': 'ಟೆಸ್ಟ್ ಐಟಂ ಪರಿಷ್ಕೃತ',
            'Grocery_Items_Eng': 'Test Item Updated',
            'Grocery_Category': 'Grocery',
            'Qtl_Kg_Ltr': 'Kg',
            'Std_Rate': 60.0
        }
        res = self.client.put('/api/grocery-items/9999', json=edit_data)
        self.assertEqual(res.status_code, 200)

        # Delete catalog item
        res = self.client.delete('/api/grocery-items/9999')
        self.assertEqual(res.status_code, 200)
        self.logout()

    def test_06_inward_stock_flow(self):
        """Test stock inward transaction logging and automatic stock updates"""
        self.login('head', '123')
        
        # Select or create a master item for stock test
        db_query("INSERT OR IGNORE INTO Grocery_Items (Grocery_Code, Grocery_Items_Kan, Grocery_Items_Eng, Grocery_Category, Qtl_Kg_Ltr, Tot_Stock, Tot_Issue, Std_Rate) VALUES (9990, 'Stock Test Item', 'Stock Test Item', 'Grocery', 'Kg', 0, 0, 10.0)", fetch=False)
        
        # Log stock inward
        inward_data = {
            'Grocery_Code': 9990,
            'Shop_Donor_ID': 999999,
            'Quantity': 100.0,
            'Purchase_Rate': 12.5,
            'Purchased_Donation': 'Purchase',
            'Remarks': 'Test Inward',
            'Date': '2026-07-24',
            'Bill_No': 'TESTBILL101',
            'Bill_Date': '2026-07-24'
        }
        res = self.client.post('/api/godown-stock', json=inward_data)
        self.assertEqual(res.status_code, 200, res.data.decode('utf-8'))

        # Verify master item's Tot_Stock is updated
        res = self.client.get('/api/grocery-items')
        items = json.loads(res.data.decode('utf-8'))
        test_item = [r for r in items if r['Grocery_Code'] == 9990][0]
        self.assertEqual(float(test_item['Tot_Stock']), 100.0)

        # Get inwards log and find the record ID
        res = self.client.get('/api/godown-stock')
        inwards = json.loads(res.data.decode('utf-8'))
        test_inward = [r for r in inwards if r['Grocery_Code'] == 9990][0]
        rec_id = test_inward['Rec']

        # Delete inward stock log and verify stock decreases back to 0
        res = self.client.delete(f'/api/godown-stock/{rec_id}')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/api/grocery-items')
        items = json.loads(res.data.decode('utf-8'))
        test_item = [r for r in items if r['Grocery_Code'] == 9990][0]
        self.assertEqual(float(test_item['Tot_Stock']), 0.0)

        # Clean up catalog item
        self.client.delete('/api/grocery-items/9990')
        self.logout()

    def test_07_vegetable_crud(self):
        """Test vegetable inward transactions logging and deletion"""
        self.login('head', '123')

        veg_data = {
            'Inst_ID': 1,
            'V_Code': 'Potato',
            'Quantity': 50.0,
            'Rate': 25.0,
            'Bill_No': 'VEGBILL-01',
            'Date': '2026-07-24',
            'Remarks': 'Potato test inwards'
        }
        res = self.client.post('/api/vegetables', json=veg_data)
        self.assertEqual(res.status_code, 200)

        # Get vegetable logs
        res = self.client.get('/api/vegetables')
        self.assertEqual(res.status_code, 200)
        logs = json.loads(res.data.decode('utf-8'))
        test_log = [r for r in logs if r['V_Code'] == 'Potato'][0]
        rec_id = test_log['Rec']

        # Delete vegetable log
        res = self.client.delete(f'/api/vegetables/{rec_id}')
        self.assertEqual(res.status_code, 200)
        self.logout()

    def test_08_bills_crud(self):
        """Test bills transaction log CRUD operations"""
        self.login('head', '123')

        bill_data = {
            'Shop_Donor_ID': 999999,
            'Bill_No': 'TESTBILL-88',
            'Bill_Date': '2026-07-24',
            'Bill_Amount': 1500.0,
            'Paid_By': 'Head Office',
            'Ch_No': 'CHQ-888999',
            'Ch_Date': '2026-07-24',
            'Ch_Amount': 1500.0,
            'Paid': 'Yes',
            'Remarks': 'Test Bill Details'
        }
        res = self.client.post('/api/bills', json=bill_data)
        self.assertEqual(res.status_code, 200)

        # Verify bill retrieval
        res = self.client.get('/api/bills')
        self.assertEqual(res.status_code, 200)
        bills = json.loads(res.data.decode('utf-8'))
        test_bill = [r for r in bills if r['Bill_No'] == 'TESTBILL-88'][0]
        rec_id = test_bill['Rec']

        # Delete bill
        res = self.client.delete(f'/api/bills/{rec_id}')
        self.assertEqual(res.status_code, 200)
        self.logout()

    def test_09_indents_complete_flow(self):
        """Test complete workflow: Raise Indent -> Approve -> Acknowledge Receipt"""
        # Create a test item with stock in central godown
        self.login('head', '123')
        db_query("INSERT OR IGNORE INTO Grocery_Items (Grocery_Code, Grocery_Items_Kan, Grocery_Items_Eng, Grocery_Category, Qtl_Kg_Ltr, Tot_Stock, Tot_Issue, Std_Rate) VALUES (9995, 'Indent Item', 'Indent Item', 'Grocery', 'Kg', 100, 0, 15.0)", fetch=False)
        self.logout()

        # Step 1: Raise Indent as Boys Hostel (inst_id = 1)
        self.login('boyshostel', '123')
        indent_data = {
            'Grocery_Code': 9995,
            'Quantity': 20.0,
            'Remarks': 'Required for Boys Hostel kitchen'
        }
        res = self.client.post('/api/indents', json=indent_data)
        self.assertEqual(res.status_code, 200)
        
        # View own store raised indents
        res = self.client.get('/api/indents')
        self.assertEqual(res.status_code, 200)
        indents = json.loads(res.data.decode('utf-8'))
        test_indent = [r for r in indents if r['Grocery_Code'] == 9995][0]
        rec_id = test_indent['Rec']
        self.assertEqual(test_indent['Sanctioned'], 'Pending')
        self.logout()

        # Step 2: Approve and dispatch indent as Godown clerk
        self.login('godown', '123')
        res = self.client.post(f'/api/indents/{rec_id}/approve', json={
            'Sanctioned_Quantity': 15.0 # Approve only 15 instead of 20 requested
        })
        self.assertEqual(res.status_code, 200)

        # Check that central stock Tot_Issue increased, Tot_Stock decreased
        res = self.client.get('/api/grocery-items')
        items = json.loads(res.data.decode('utf-8'))
        item = [r for r in items if r['Grocery_Code'] == 9995][0]
        self.assertEqual(float(item['Tot_Stock']), 85.0)
        self.assertEqual(float(item['Tot_Issue']), 15.0)
        self.logout()

        # Step 3: Acknowledge transfer receipt as Boys Hostel
        self.login('boyshostel', '123')
        res = self.client.post(f'/api/indents/{rec_id}/acknowledge')
        self.assertEqual(res.status_code, 200)

        # Check store stock balance for boyshostel (inst_id = 1)
        res = self.client.get('/api/hostel-stock/1')
        self.assertEqual(res.status_code, 200)
        store_stock = json.loads(res.data.decode('utf-8'))
        stock_record = [r for r in store_stock if r['Grocery_Code'] == 9995][0]
        self.assertEqual(float(stock_record['CurrentBalance']), 15.0)

        # Step 4: Clean up test indent and test item
        self.logout()
        self.login('head', '123')
        self.client.delete(f'/api/indents/{rec_id}')
        self.client.delete('/api/grocery-items/9995')
        self.logout()

if __name__ == '__main__':
    unittest.main()
