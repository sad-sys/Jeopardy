import pandas as pd

# Load the data
df = pd.read_csv("jeopardySmall.csv")

# Function to pick a game based on the air date
def pickGame(airDate, df):
    return df[df[' Air Date'].str.strip() == airDate]

# Function to list unique categories within a game
def listCategories(game):
    categories = game['Category'].unique()
    return categories

# Function to pick questions from a specific category within a game
def pickCategory(category, game):
    return game[game[' Category'].str.strip() == category]

# Function to pick a value from a particular category
def pickQuestionRow(category, value):
    return category[category[' Value'].str.strip() == value]

# Main game function
'''
def main():
    while True:
        air_date = input("Enter the air date of the game (YYYY-MM-DD) or 'exit' to quit: ").strip()
        if air_date.lower() == 'exit':
            break
        
        game = pickGame(air_date, df)
        if game.empty:
            print(f"No game found for the date {air_date}. Please try again.")
            continue
        
        categories = listCategories(game)
        print("Available categories:")
        for i, cat in enumerate(categories):
            print(f"{i+1}. {cat}")
        
        cat_index = int(input("Select a category by number: ")) - 1
        if cat_index < 0 or cat_index >= len(categories):
            print("Invalid category selection. Please try again.")
            continue
        
        category = categories[cat_index]
        category_questions = pickCategory(category, game)
        
        values = category_questions[' Value'].unique()
        print(f"Available values in '{category}': {', '.join(values)}")
        
        value = input("Enter the value of the question you want to answer: ").strip()
        questionRow = pickQuestionRow(category_questions, value)
        
        if not questionRow.empty:
            question = questionRow[' Question'].values[0]
            correct_answer = questionRow[' Answer'].values[0]
            
            print(f"Question: {question}")
            user_answer = input("Your answer: ").strip()
            
            if user_answer.lower() == correct_answer.lower():
                print("Correct!")
            else:
                print(f"Incorrect. The correct answer was: {correct_answer}")
        else:
            print("No question found for the given category and value. Please try again.")

# Run the main function
main()
'''