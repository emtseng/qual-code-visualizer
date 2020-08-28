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
  """

  # Manual mappings for Remote Clinic paper
  if "Checkup" in code:
    new_code = urlSafe( stripQuotesSpace( "Privacy checkups" ) )
    codeCorrections[code] = new_code
    print "Replacing '" + codeCorrections[code] + "' with '" + code + "'"
    return new_code, codeCorrections

  # General code corrections
  if( code in codeCorrections ):
    print "Using '" + codeCorrections[code] + "' instead of '" + code + "'"
    code = codeCorrections[code]
    return code, codeCorrections

  if skip:
    return '', codeCorrections

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
