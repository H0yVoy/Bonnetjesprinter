Features:
- telegram berichten
- weather updates
- netwerk printen (vanaf foon ofzo)/http
- coole web interface waar je dingen kunt uploaden enz
- esp
- user authentication for telegram bot
- sleeping hours for telegram bot
- stats:
  bot:
    - prints per user
    - characters per user
    - paper per user
  total print
  import network


implementation:
- commands that each trigger a different function such as 
  /weather (met binnentemperatuur)
  /motivation
  /idk?
  etc.
these could be made available for specific user groups,
and be triggered from a web interface easily as well


#authentication
for every /start, save id, name, etc to check in database
check for every message if person is allowed printer

features:
- config in een bestand storen zou cool zijn
- in deze config ook andere dingen zetten: cut na bericht ja/nee
- access revoken
- staaaaaaaaats
- silent hours
- pics