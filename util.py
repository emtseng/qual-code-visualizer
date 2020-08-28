import editdistance

def urlSafe( string ):
  urlSafe = string.strip()
  urlSafe = urlSafe.replace( '/', '_' )
  urlSafe = urlSafe.replace( '?', '_' )
  urlSafe = urlSafe.replace(":", ' -')
  urlSafe = urlSafe.replace( ' ', '_' )
  urlSafe = urlSafe.replace('%', '')
  urlSafe = urlSafe.replace('"', '')
  urlSafe = urlSafe.replace("'", '')
  return urlSafe

def stripQuotesSpace( string ):
  if( len(string) < 2 ):
    return string.strip()
  if( string[0] == '"' and string[-1] == '"' ):
    return string[1:-1].strip()
  return string.strip()

def mergeCodes( code, codes, codeCorrections, skip=False ):
  """
    If an unrecognized code is found in a transcript file, check for nearby ones by edit distance. 
    Customizable by project.

    :param code: slugified code
    :param codes: list of all codes
    :param codeCorrections: dict of corrections seen so far
    :param skip: bool for whether to just skip codes you haven't seen or try to map them
  """
  # If you've seen this codeCorrection in your cache, use the cached correction
  if( code in codeCorrections ):
    # print "Using '" + codeCorrections[code] + "' instead of '" + code + "'"
    code = codeCorrections[code]
    return code, codeCorrections

  if skip:
    return '', codeCorrections

  # Manual mappings for Remote Clinic paper
  mappings = {
    "Checkup": "Privacy checkups",
    "Out of scope": "Client's concern is out of clinic scope",
    "Consultant educates client on tech": "Consultant as educator",
    "Connection issue": "Challenge: Remote connection difficulties",
    "Consultant unfamiliar with a given platform / technology": "Consultant unfamiliarity with specific platforms (e.g. Android vs. iOS / Windows vs Mac)",
    "Not enough time": "Not enough time / Prioritization",
    "Clients expectations": "Challenge: Managing clients' expectations",
    "TAQ": "Using TAQ / Technograph",
    "Maintaining anonymity": "Anonymity: Preserving",
  }

  dumped = [urlSafe( stripQuotesSpace( k ) ) for k in [
    "Client concern",
    "footprint",
    "translator",
    "Devices",
    "Social media accounts",
    "Client confirms intake",
    "Email accounts",
    "Cloud accounts",
  ]]

  # First remove dumped codes
  for dumped_code in dumped:
    slugged = urlSafe( stripQuotesSpace( dumped_code ) )
    if slugged in code:
      return '', codeCorrections

  # Then process mappings
  for k, v in mappings.items():
    slugged = urlSafe( stripQuotesSpace( k ) )
    if slugged in code:
      new_code = urlSafe( stripQuotesSpace( v ) )
      codeCorrections[code] = new_code
      print "Replacing '" + code + "' with '" + new_code + "'"
      return new_code, codeCorrections

  #print "Unrecognized code: ", code
  distances = {}
  for possibleCode in codes:
    distances[editdistance.eval( code, possibleCode )] = possibleCode

  for i, key in enumerate(sorted(distances)):
    #if( i > 2 ):   # only bother the user to go through top 3 closest codes
    #  break
    #answer = raw_input("Should '" + code + "' have been '" + distances[key] + "'?  [y/N] ")
    #if( answer == 'y' or answer == 'Y' ):
    print "Replacing '"+ code +"' with '" + distances[key] + "'"
    codeCorrections[code] = distances[key]
    code = distances[key]
    return code, codeCorrections  # It's always working well with edit distance, so let's just do it without asking

  return '', codeCorrections  # Signifies no suitable match found
