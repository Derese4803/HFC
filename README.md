# HFC
1. Upload constraints.csv (Range & Data Type Violations)
The constraints file contains data that is physically or logically impossible based on standalone business rules. It flags errors where an entered number falls outside a normal, acceptable range.

The Logic: It evaluates a single data point against a fixed threshold rule (e.g., minimum or maximum boundaries).

Example: A field agent inputs a farmer's age as 180 or a phone number with only 3 digits.

How it looks in the app: The app calculates the allowed boundary from the rule (e.g., age must be between 18 and 100) and warns the enumerator if their corrected value still breaks the rule.

2. Upload logic.csv (System Mismatches & Reconciliation)
The logic file tracks discrepancies between two different data sources that should match but don't. It is used for cross-checking and system reconciliation.

The Logic: It compares a value reported by the field agent against an existing baseline record already stored in the system database (referred to in the code as the "Troster Value").

Example: The field agent reports that a farmer delivered 50 bags of crops, but the warehouse digital scale/system record shows they only checked in 35 bags.

How it looks in the app: The app displays a side-by-side comparison using metrics cards showing "Your Report", "System Record", and the calculated "Difference" (Delta) so the agent can figure out which number is correct.
 Step 1: Upload Baseline System Datasets
Step 2: Select Your Enumerator Identifier Code
Once the datasets are loaded, the system reads the username column inside your CSV files and automatically builds a dynamic menu.

What you do: Click the drop-down menu labeled "Select Your Enumerator Identifier Code:" and pick your assigned username or ID.

What the system does: The app instantly filters out thousands of irrelevant rows and isolates only the specific data errors linked to your identity.

🛠️ The Rest of the Workflow
Once Step 2 is complete, you will proceed through these final stages to finish cleansing your data:

Step 3: Audit the Error Backlog
The system opens up your customized Pending Data Verification Backlog. You will see expandable cards for every farmer record that contains an error.

For Constraints: You will see what invalid numbers were typed (e.g., an impossible age or flag).

For Logic: You will see side-by-side comparison cards showing "Your Report" vs. the "System Record" so you can visually spot the discrepancy.

Step 4: Input Corrections & Justifications
Inside each farmer's card, you perform the actual correction:

Type the updated, verified metric into the "Corrected Value" field.

Type an operational note in the "Explanation (Required)" box explaining why the change happened (e.g., "Farmer confirmed delivery error via phone recall").

Step 5: Commit and Export
Field Agents: Click "Commit Correction". The error disappears from your screen and moves into the master database.

Administrators: Log into the sidebar using the Admin Login Dashboard to view system-wide performance metrics and click the Download Master Corrections Log button to save the finalized data as an Excel/CSV spreadsheet.
