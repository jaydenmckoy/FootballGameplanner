import os
import pandas as pd
from numpy import nan
from weasyprint import HTML

sheet_columns = [
    # "PLAY #",
    # "YARD LN",
    "ODK",
    "DN",
    "DIST",
    # "HASH",
    "OFF FORM",
    "BACKFIELD",
    "OFF PLAY",
    "PLAY TYPE",
    "ROUTES",
    # "RESULT",
    # "GN/LS",
    # "EFF",
]

outpath = './output'

slot_receivers = ['S','R','W']

class GamePlanner:

  def __init__(self,data_path):
    print('Importing data')
    self.data_path = data_path
    self.import_data()
    print('Generating Game Plan')
    # self.generate_gameplan()
    routes_by_form_and_backset = self.gp_routes_by_formation_and_backset3()
    print('\n\n***Routes by formation and backset:')
    print(routes_by_form_and_backset)
    GamePlanner.table_to_pdf(routes_by_form_and_backset,'Routes by formation and backset')

  @staticmethod
  def table_to_pdf(df,title):
     html_text = df.to_html()
     HTML(string=html_text).write_pdf('./output/test.pdf')
     


  def import_data(self):
    files = [x for x in os.listdir(self.data_path) if x.endswith('.xlsx')]
    files.sort()
    game_data = pd.DataFrame()
    for game_number,fn in enumerate(files):
      # Read data
      df = pd.read_excel(os.path.join(self.data_path,fn),sheet_name='Sheet1',engine='openpyxl')
      # Clean data
      df = GamePlanner.__clean_sheet(df)
      # Game specific columns
      fn_split = fn.split()
      df['date'] = '-'.join(fn_split[:3])
      df['oppenent'] = fn[-1]
      df['Game No.'] = game_number
      # Concat
      game_data = pd.concat([game_data,df])
    # Return
    self.data = game_data

  @staticmethod
  def __clean_sheet(df):
    # Parse defensive plays
    df = df[df['ODK'] == 'O']
    # Set columns
    df = df[sheet_columns]
    # Replace Routes slash
    route_idx = df[pd.isna(df['ROUTES']) == False].index
    df.loc[route_idx,'ROUTES'] = df.loc[route_idx,'ROUTES'].str.replace('/','-')
    # Return
    return df

  def generate_gameplan(self):
    # Summary
    summary = self.gp_summary()
    print('\n***Summary:')
    for name,df in summary.items():
      print(f'\n-{name}')
      print(df)
    # Down and distance plays and routes
    dnd_plays_and_routes = self.gp_dnd_plays_and_routes()
    print('\n\n***Down and distance plays and routes:')
    print(dnd_plays_and_routes)
    # Down and distance
    dnd = self.gp_down_and_distance()
    print('\n\n***Down and distance:')
    print(dnd)
    # Routes by formation and backset
    routes_by_form_and_backset = self.gp_routes_by_formation_and_backset()
    print('\n\n***Routes by formation and backset:')
    print(routes_by_form_and_backset)
    # # Motion plays
    # motion_plays = self.gp_motion_plays()
    # print('\n\n***Motion plays:')
    # print('-Tight:')
    # print(motion_plays['tight'])
    # print('Up')
    # print(motion_plays['up'])

  def gp_summary(self):
    df = self.data.copy()
    summary = {}
    total = len(df)
    # --- Run/Pass Totals ---
    run_total  = df['PLAY TYPE'].value_counts().get('Run',   0)
    pass_total = df['PLAY TYPE'].value_counts().get('Pass',  0)
    run_row  = [round(run_total/total*100,1), f'{run_total}/{total}']
    pass_row = [round(pass_total/total*100,1),f'{pass_total}/{total}']
    # Create dataframe
    summary['Run/Pass'] = pd.DataFrame(
        data  = [run_row,pass_row],
        index = ['Run','Pass'],
        columns=['%','Count'])
    # --- Top Plays ---
    play_counts = df['OFF PLAY'].value_counts()
    top_plays = pd.DataFrame()
    top_plays['%'] = (play_counts/total*100).round(1)
    top_plays['Count'] = play_counts.astype(str) + f'/{total}'
    summary['Top Plays'] = top_plays
    # Return
    return summary

  def gp_down_and_distance(self):
    columns = ['DN','DIST','PLAY TYPE']
    df = self.data[columns].copy()
    # Define the distance ranges
    bins = [0, 6, 10, float('inf')]
    labels = ['0-6', '7-10', '10+']
    # Create a new column with distance ranges
    df.loc[:, 'DISTANCE'] = pd.cut(df['DIST'], bins=bins, labels=labels, right=False)
    # Group by 'DN', 'DIST Range', and 'PLAY TYPE'
    grouped = df.groupby(['DN', 'DISTANCE', 'PLAY TYPE']).size().unstack(fill_value=0).reset_index()
    # Calculate run/pass percentage
    grouped['total']  = grouped['Run'] + grouped['Pass']
    grouped['Run %']  = (grouped['Run'] / grouped['total']) * 100
    grouped['Pass %'] = (grouped['Pass'] / grouped['total']) * 100
    grouped['Run %']  = grouped['Run %'].round(0)
    grouped['Pass %'] = grouped['Pass %'].round(0)
    # Return
    return grouped

  def gp_routes_by_formation_and_backset(self):
    columns = ['OFF FORM','BACKFIELD','ROUTES']
    df = self.data[columns].copy()
    # Group
    grouped = df.groupby(['OFF FORM', 'BACKFIELD', 'ROUTES']).size().reset_index(name='COUNT')
    print('gp_routes_by_formation_and_backset grouped\n',grouped)
    # You can also calculate percentages within each group if needed
    grouped['TOTAL'] = grouped.groupby(['OFF FORM', 'BACKFIELD'])['COUNT'].transform('sum')
    grouped['PERCENTAGE'] = (grouped['COUNT'] / grouped['TOTAL']) * 100
    grouped['PERCENTAGE'] = grouped['PERCENTAGE'].round(1)
    grouped.set_index(['OFF FORM','BACKFIELD','ROUTES'], inplace=True)
    # Return
    return grouped

  def gp_motion_plays(self):
    df = self.data.copy()
    motion_plays = {}
    # Label tight/up plays
    df['up']    = df[df['OFF FORM'].contains('U')]
    df['tight'] = df[df['OFF FORM'].contains(slot_receivers) & (not df['up'])]
    # Return
    return {'tight': None, 'Up': None}

  def gp_dnd_plays_and_routes(self):
    df = self.data[['DN','DIST','OFF FORM','BACKFIELD','OFF PLAY','ROUTES']].copy()
    # Define the distance ranges
    bins = [0, 6, 10, float('inf')]
    labels = ['0-6', '7-10', '10+']
    # Create a new column with distance ranges
    df['ROUTES'] = df['ROUTES'].fillna(0)
    df.loc[:, 'DISTANCE'] = pd.cut(df['DIST'], bins=bins, labels=labels, right=False)
    # df.drop(columns='DIST',inplace=True)
    # print('plays and routes df\n',df)
    # grouped = df.groupby(['DN', 'DISTANCE', 'OFF FORM', 'BACKFIELD', 'OFF PLAY'])['ROUTES'].value_counts().reset_index(name='COUNT')
    # grouped['TOTAL'] = grouped.groupby(['DN', 'DISTANCE', 'OFF FORM', 'BACKFIELD', 'OFF PLAY'])['COUNT'].transform('sum')
    # grouped['PERCENTAGE'] = (grouped['COUNT'] / grouped['TOTAL']) * 100
    # grouped['PERCENTAGE'] = grouped['PERCENTAGE'].round(1)

    # grouped.set_index(['DN', 'DISTANCE', 'OFF FORM', 'BACKFIELD', 'OFF PLAY', 'ROUTES'], inplace=True)

    # Group by 'DN,' 'DISTANCE,' 'OFF FORM,' 'BACKFIELD,' and 'OFF PLAY' and count 'ROUTES' within each group
    grouped = df.groupby(['DN', 'DISTANCE', 'OFF FORM', 'BACKFIELD', 'OFF PLAY', 'ROUTES']).size().reset_index(name='ROUTE COUNT')

    # Set the columns as a multilevel index
    grouped.set_index(['DN', 'DISTANCE', 'OFF FORM', 'BACKFIELD', 'OFF PLAY', 'ROUTES'], inplace=True)

    # Calculate the total count for each subindex group
    total_counts = grouped.groupby(['DN', 'DISTANCE', 'OFF FORM', 'BACKFIELD', 'OFF PLAY']).sum()

    # Calculate the percentage of occurrence within each subindex group
    grouped['PERCENTAGE'] = (grouped['ROUTE COUNT'] / total_counts['ROUTE COUNT']) * 100



    # Return
    return grouped

  def gp_routes_by_formation_and_backset2(self):
      columns = ['OFF FORM','BACKFIELD','ROUTES']
      df = self.data[columns].copy()
      df['ROUTES'] = df['ROUTES'].fillna(0)

      # Calculate the percentage of each 'BACKFIELD' by 'OFF FORM' (FORMATION)
      backfield_percentage_by_off_form = (df.groupby(['OFF FORM', 'BACKFIELD']).size() / df.groupby('OFF FORM').size()) * 100
      # Reset the index and rename the columns
      backfield_percentage_by_off_form = backfield_percentage_by_off_form.reset_index()
      backfield_percentage_by_off_form.columns = ['OFF FORM', 'BACKFIELD', 'BACKFIELD PERCENTAGE']

      # Calculate the total percentage by 'OFF FORM'
      total_percentage_by_off_form = df.groupby('OFF FORM').size() / len(df) * 100
      total_percentage_by_off_form = total_percentage_by_off_form.reset_index()
      total_percentage_by_off_form.columns = ['OFF FORM', 'TOTAL PERCENTAGE']

      # Merge the total percentage information into the DataFrame
      backfield_percentage_by_off_form = pd.merge(backfield_percentage_by_off_form, total_percentage_by_off_form, on='OFF FORM')

      backfield_percentage_by_off_form.set_index(['OFF FORM', 'BACKFIELD'], inplace=True)
      print(backfield_percentage_by_off_form)

      # Return
      return None
  
  def gp_routes_by_formation_and_backset3(self):
      columns = ['OFF FORM','BACKFIELD','ROUTES']
      df = self.data.copy()
      df = df[columns]
      df = df[pd.isna(df['ROUTES'])==False]
      df.reset_index(inplace=True)

      # Calculate the percentage of each 'BACKFIELD' by 'OFF FORM' (FORMATION)
      backfield_percentage_by_off_form = (df.groupby(['OFF FORM', 'BACKFIELD']).size() / df.groupby('OFF FORM').size()) * 100
      # Reset the index and rename the columns
      backfield_percentage_by_off_form = backfield_percentage_by_off_form.reset_index()
      backfield_percentage_by_off_form.columns = ['OFF FORM', 'BACKFIELD', 'BACKFIELD PERCENTAGE']

      # Calculate the total percentage by 'OFF FORM'
      total_percentage_by_off_form = df.groupby('OFF FORM').size() / len(df) * 100
      total_percentage_by_off_form = total_percentage_by_off_form.reset_index()
      total_percentage_by_off_form.columns = ['OFF FORM', 'TOTAL PERCENTAGE']

      # Calculate the percentage of 'ROUTES' by 'OFF FORM' and 'BACKFIELD'
      routes_percentage_by_off_form_and_backfield = (df.groupby(['OFF FORM', 'BACKFIELD', 'ROUTES']).size() / df.groupby(['OFF FORM', 'BACKFIELD']).size()) * 100
      # Reset the index and rename the columns for the routes percentage
      routes_percentage_by_off_form_and_backfield = routes_percentage_by_off_form_and_backfield.reset_index()
      routes_percentage_by_off_form_and_backfield.columns = ['OFF FORM', 'BACKFIELD', 'ROUTES', 'ROUTES PERCENTAGE']

      # Merge the total percentage and routes percentage information into the DataFrame
      backfield_percentage_by_off_form = pd.merge(backfield_percentage_by_off_form, total_percentage_by_off_form, on='OFF FORM')
      backfield_percentage_by_off_form = pd.merge(backfield_percentage_by_off_form, routes_percentage_by_off_form_and_backfield, on=['OFF FORM', 'BACKFIELD'])

      backfield_percentage_by_off_form.set_index(['OFF FORM', 'BACKFIELD'], inplace=True)
      # backfield_percentage_by_off_form = backfield_percentage_by_off_form.groupby(['OFF FORM', 'BACKFIELD']).reset_index()
      print(backfield_percentage_by_off_form)

      # Return
      return None
  
  def gp_routes_by_formation_and_backset3(self):
      columns = ['OFF FORM','BACKFIELD','ROUTES']
      df = self.data.copy()
      df = df[columns]
      df = df[pd.isna(df['ROUTES'])==False]
      df.reset_index(inplace=True)

      # Calculate the percentage of each 'BACKFIELD' by 'OFF FORM' (FORMATION)
      backfield_percentage_by_off_form = (df.groupby(['OFF FORM', 'BACKFIELD']).size() / df.groupby('OFF FORM').size()) * 100
      # Reset the index and rename the columns
      backfield_percentage_by_off_form = backfield_percentage_by_off_form.reset_index()
      backfield_percentage_by_off_form.columns = ['OFF FORM', 'BACKFIELD', 'BACKFIELD PERCENTAGE']

      # Calculate the total percentage by 'OFF FORM'
      total_percentage_by_off_form = df.groupby('OFF FORM').size() / len(df) * 100
      total_percentage_by_off_form = total_percentage_by_off_form.reset_index()
      total_percentage_by_off_form.columns = ['OFF FORM', 'TOTAL PERCENTAGE']

      # Calculate the percentage of 'ROUTES' by 'OFF FORM' and 'BACKFIELD'
      routes_percentage_by_off_form_and_backfield = (df.groupby(['OFF FORM', 'BACKFIELD', 'ROUTES']).size() / df.groupby(['OFF FORM', 'BACKFIELD']).size()) * 100
      # Reset the index and rename the columns for the routes percentage
      routes_percentage_by_off_form_and_backfield = routes_percentage_by_off_form_and_backfield.reset_index()
      routes_percentage_by_off_form_and_backfield.columns = ['OFF FORM', 'BACKFIELD', 'ROUTES', 'ROUTES PERCENTAGE']

      # Merge the total percentage and routes percentage information into the DataFrame
      backfield_percentage_by_off_form = pd.merge(backfield_percentage_by_off_form, total_percentage_by_off_form, on='OFF FORM')
      backfield_percentage_by_off_form = pd.merge(backfield_percentage_by_off_form, routes_percentage_by_off_form_and_backfield, on=['OFF FORM', 'BACKFIELD'])

      # Group by 'OFF FORM' and 'BACKFIELD'
      grouped_result = backfield_percentage_by_off_form.groupby(['OFF FORM', 'BACKFIELD'])

      # Print the grouped result
      for (off_form, backfield), group in grouped_result:
         print(f"OFF FORM: {off_form}, BACKFIELD: {backfield}")
         print(group)
         print("\n")

      # Return
      return None
  
  def gp_routes_by_formation_and_backset3(self):
      columns = ['OFF FORM','BACKFIELD','ROUTES']
      df = self.data.copy()
      df = df[columns]
      df = df[pd.isna(df['ROUTES'])==False]
      df.reset_index(inplace=True)
      print('\n\n***gp_routes_by_formation_and_backset3')

      # Calculate the percentage of each 'BACKFIELD' by 'OFF FORM' (FORMATION)
      backfield_percentage_by_off_form = (df.groupby(['OFF FORM', 'BACKFIELD']).size() / df.groupby('OFF FORM').size()) * 100
      # Reset the index and rename the columns
      backfield_percentage_by_off_form = backfield_percentage_by_off_form.reset_index()
      backfield_percentage_by_off_form.columns = ['OFF FORM', 'BACKFIELD', 'BACKFIELD %']

      # Calculate the total percentage by 'OFF FORM'
      total_percentage_by_off_form = df.groupby('OFF FORM').size() / len(df) * 100
      total_percentage_by_off_form = total_percentage_by_off_form.reset_index()
      total_percentage_by_off_form.columns = ['OFF FORM', 'OFF FORM %']

      # Calculate the percentage of 'ROUTES' by 'OFF FORM' and 'BACKFIELD'
      routes_percentage_by_off_form_and_backfield = (df.groupby(['OFF FORM', 'BACKFIELD', 'ROUTES']).size() / df.groupby(['OFF FORM', 'BACKFIELD']).size()) * 100
      # Reset the index and rename the columns for the routes percentage
      routes_percentage_by_off_form_and_backfield = routes_percentage_by_off_form_and_backfield.reset_index()
      routes_percentage_by_off_form_and_backfield.columns = ['OFF FORM', 'BACKFIELD', 'ROUTES', 'ROUTES %']

      # Merge the total percentage and routes percentage information into the DataFrame
      backfield_percentage_by_off_form = pd.merge(backfield_percentage_by_off_form, total_percentage_by_off_form, on='OFF FORM')
      backfield_percentage_by_off_form = pd.merge(backfield_percentage_by_off_form, routes_percentage_by_off_form_and_backfield, on=['OFF FORM', 'BACKFIELD'])

      # Group by 'OFF FORM' and 'BACKFIELD'
      grouped_result = backfield_percentage_by_off_form.groupby('OFF FORM')

      # Print the grouped result
      data = []
      for off_form,of_group in grouped_result:
         # p = of_group.loc[of_group.index[0],'OFF FORM %'].round(1)
         # d = [off_form,nan,nan,p]
         # data.append(d)
         data.append([off_form,nan,nan,of_group.loc[of_group.index[0],'OFF FORM %']])
         # print(off_form,of_group.loc[of_group.index[0],'OFF FORM %'])
         for backfield, bf_group in of_group.groupby('BACKFIELD'):
            data.append([nan,backfield,nan,bf_group.loc[bf_group.index[0],'BACKFIELD %']])
            route_data = bf_group[['ROUTES','ROUTES %']].values.tolist()
            route_data = [[nan,nan,x[0],x[1]] for x in route_data]
            data.extend(route_data)
      result = pd.DataFrame(data,columns=['Formation','Backset','Routes','%'])
      result['%'] = result['%'].round(1)
      # print(result)
      # Return
      return result


data_path = '/home/jmckoy/Documents/Football/Gameplans/GP_VMC_2023_09_22/game_data'
vmc_week_3 = GamePlanner(data_path)