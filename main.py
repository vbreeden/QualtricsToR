# This is the main file for the Qualtrics-to-R data processor.
import configparser
import pandas as pd
from collections import Counter


def load_dataframe(csv_file, drop_columns, df_columns):
    # Qualtrics output contains a header row and question row that we want to remove.
    header_row = 0
    question_row = 1

    # The first line should contain the path to the qualtrics output.
    # Use this path to generate the dataframe, and then remove the header row and
    # question row.
    df = pd.read_csv(csv_file)
    df = df.drop([header_row, question_row])
    participants = df.shape[0]

    # Remove the unusable columns from the data.
    for drop_column in drop_columns:
        df.drop(drop_column, axis=1, inplace=True)

    # In my data I have freeform responses that I need to remove when preparing the data for R.
    # Comment or uncomment and modify as needed to fit your project.
    question = 'Q143.'
    first_subpart = 2
    last_subpart = 17
    for i in range(first_subpart, last_subpart, 1):
        freeform_column = question + str(i)
        df.drop(freeform_column, axis=1, inplace=True)

    # Create the dataframe that will be used for export.
    study_df = pd.DataFrame(columns=df_columns)

    # My qualtrics study is formatted to retrieve multiple datapoints per question.
    # For example. Q3.1 is a dance choice response, Q3.2 is a monolithic/polylithic choice response,
    # and Q3.3 is a "I did or did not recognize the song response".
    # This code will need to be changed to match the format of your qualtrics questions.
    # first_question and last_question correspond to the question number in qualtrics for
    # your survey.
    stimuli_number = 1
    first_question = 3
    last_question = 143
    for i in range(first_question, last_question, 1):
        # Create a temporary dataframe
        temp_df = pd.DataFrame(columns=df_columns)

        # Set the current question header values
        dance_header = 'Q' + str(i) + '.1'
        monopoly_header = 'Q' + str(i) + '.2'
        recognized_header = 'Q' + str(i) + '.3'

        # Convert the associated value to a list.
        dance_list = df[dance_header].tolist()
        monopoly = df[monopoly_header].tolist()
        recognized = df[recognized_header].tolist()

        # Store the lists in the temp dataframe
        temp_df[df_columns[0]] = dance_list
        temp_df[df_columns[1]] = monopoly
        temp_df[df_columns[2]] = recognized

        study_df = study_df.append(temp_df, ignore_index=True)

    return study_df, participants


def export_data(study_df, output_columns, output_file, participants):
    songs_per_genre = 10
    songs_per_category = 70
    export_df = pd.DataFrame(columns=output_columns)

    mono_poly = study_df[output_columns[0]].tolist()
    recognized = study_df[output_columns[1]].tolist()
    
    # This is where the magic happens for getting the data into an R-friendly format.
    mono_list = []
    recognized_list = []
    for i in range(0, len(study_df), participants):
        mono_list.append((Counter(mono_poly[i:i + participants]))['Only the selected dance genre.'])
        recognized_list.append((Counter(recognized[i:i + participants]))['Yes'])

    export_df[output_columns[0]] = mono_list
    export_df[output_columns[1]] = recognized_list
    export_df.to_csv(output_file, index=False)


if __name__ == "__main__":
    # Read the config file used for parsing Qualtrics output
    config = configparser.ConfigParser()
    config.read('config.txt')
    csv_file = config.get('QualInputPath', 'input_file')
    drop_columns = list(filter(None, [x.strip() for x in config.get('DropColumns', 'columns').splitlines()]))
    df_columns = list(filter(None, [x.strip() for x in config.get('DataframeColumns', 'columns').splitlines()]))
    output_columns = list(filter(None, [x.strip() for x in config.get('OutputColumns', 'columns').splitlines()]))
    output_file = config.get('OutputPath', 'output_file')

    study_df, participants = load_dataframe(csv_file, drop_columns, df_columns)
    export_data(study_df, output_columns, output_file,  participants)
