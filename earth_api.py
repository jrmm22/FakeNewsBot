from flask import Flask, render_template
import tweepy, time, sys
from time import sleep
from random import randint
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream 
from flask import jsonify
import flask
import time
import datetime
import re
from flask import request
import os
import io
import sys

import urllib3
import urllib 

BITLYTOK=''

###
### Se definen las siguientes tres funciones para mandar mensajes a usuarios.
### Para DM se requiere que sean seguidores del bot, asi que se revisa si existen en la lista
### de seguidores.
### 

#La siguiente es una lista de influencers, es decir
#gente a la que se le enviaran las notificaciones.
influencers = []
influencers_onlyurgent = []

#La siguiente es una lista de los usuarios que nos siguen
# Se usa para saber si podemos mandar mensajes privados o no.
followed_by = [""]

#Estas son las tablas que vamos a leer de la tabla
tabs=[ "urgencias", "albergues", "centros", "otros", "ofrecimientos" ]
#Y estos son los ultimos IDs que leimos en cada tabla.
proc_ids=[ 0, 0, 0, 0, 0 ]
proc_stamps=[ 0, 0, 0, 0, 0 ]

def load_last_stamps():
    idfiles = open( "tabs_stamps.txt", "rt" )
    if idfiles:
        
        idfiles_data  = flask.json.loads( idfiles.readline() )

        proc_stamps[ 0 ] = idfiles_data[ "centros" ]
        proc_stamps[ 1 ] = idfiles_data[ "urgencias" ]
        proc_stamps[ 2 ] = idfiles_data[ "albergues" ]
        proc_stamps[ 3 ] = idfiles_data[ "otros" ]
        proc_stamps[ 4 ] = idfiles_data[ "ofrecimientos" ]

        print( "Detected {} {} {} {} {}".format( proc_stamps[0], proc_stamps[1], proc_stamps[2], proc_stamps[3], proc_stamps[4] ) );
        idfiles.close()

def load_last_ids():
    idfiles = open( "tabs_ids.txt", "rt" )
    if idfiles:
        
        idfiles_data  = flask.json.loads( idfiles.readline() )

        proc_ids[ 0 ] = idfiles_data[ "centros" ]
        proc_ids[ 1 ] = idfiles_data[ "urgencias" ]
        proc_ids[ 2 ] = idfiles_data[ "albergues" ]
        proc_ids[ 3 ] = idfiles_data[ "otros" ]
        proc_ids[ 4 ] = idfiles_data[ "ofrecimientos" ]

        print( "Detected {} {} {} {} {}".format( proc_ids[0], proc_ids[1], proc_ids[2], proc_ids[3], proc_ids[4] ) );
        idfiles.close()

def generate_last_stamps( ):
    cur_stamp = time.time( ) - 3600 #1 hr ago
    proc_stamps[ 0 ] = cur_stamp
    proc_stamps[ 1 ] = cur_stamp
    proc_stamps[ 2 ] = cur_stamp
    proc_stamps[ 3 ] = cur_stamp
    proc_stamps[ 4 ] = cur_stamp

def store_last_stamps( ):
    idfiles = open( "tabs_stamps.txt", "wt" )
    if idfiles:
        asstring = "{{ \"centros\":{}, \"urgencias\":{}, \"albergues\":{}, \"otros\":{}, \"ofrecimientos\":{} }}".format( proc_stamps[0], proc_stamps[1], proc_stamps[2], proc_stamps[3], proc_stamps[4] )
        print( "Stored {} ".format( asstring ) );
        idfiles.write( asstring )
        idfiles.close
    
def store_last_ids( ):
    idfiles = open( "tabs_ids.txt", "wt" )
    if idfiles:
        asstring = "{{ \"centros\":{}, \"urgencias\":{}, \"albergues\":{}, \"otros\":{}, \"ofrecimientos\":{} }}".format( proc_ids[0], proc_ids[1], proc_ids[2], proc_ids[3], proc_ids[4] )
        print( "Stored {} ".format( asstring ) );
        idfiles.write( asstring )
        idfiles.close
    
def check_if_str_valid( var ):
    result = False
    if var:
        if len( var ) > 2:
            result = True
    return result

def bitly_my_url( url ):
    bitly_address = "https://api-ssl.bitly.com"
    bitly_address += "/v3/shorten?access_token="+ BITLYTOK + "&longUrl=" + urllib.parse.quote_plus( url ) + "&format=txt"
    req = http.request( 'GET', bitly_address )
    
    result = req.data.decode( )
#    print( "My long address {} is now {}".format( url, result ) );
#    print( "Queried {}".format( bitly_address ) )
    return result


# La siguiente funcion permite limitar el trafico, para no exceder el limite
def rate_limit( cursor ):
    while True:
        try:
            yield cursor.next()
        except:
            print( "ZZZzzz" );
            time.sleep( 30 )

def populate_my_follower_list():
    # Usamos nuestra rate_limit para revisar los seguidores q tenemos.
    for f in rate_limit( tweepy.Cursor(api.followers).items() ):
        print( "Found follower {}".format( f.screen_name ) )
        followed_by.append( '@' + f.screen_name )

def send_image( api, imgurl, message, can_i_shorten, wait_for_rate ):
    result = False
    filename = 'temp.png'
    req = http.request( 'GET', imgurl )
    if req:
        msg = message
        msglen = len( msg )

        if can_i_shorten :
            if msglen >= 140 :
                msg = msg[0:135] + "..."
        
        with open( filename, "wb" ) as im:
            im.write( req.data )
            im.flush( )


#        print( "sending msg {} with len {}".format( msg, len( msg )  ) )
#        print( "original msg {} with image {}".format( message, imgurl  ) )
        done = False

        while done == False:
            try:
                api.update_with_media( filename, status=msg )
                result = True
                done = True
            except tweepy.RateLimitError:
                if wait_for_rate:
                    print( "Rate limit reached. Waiting 1 min" );
                    time.sleep( 60 )
                else:
                    done = True
            except:
                print( "Something failed tweeting msg :{}: len {} img {}".format( msg, len(msg), imgurl ) )
                done = True
        #os.remove( filename )
        im.close()
    return result

def send_private_or_public( tweepy_api, user, msg, as_private, as_public, wait_for_rate ):
    result = False
    # Checamos que el usuario al que queremos mandar mensaje privado en efecto 
    # pueda recibirlos
    done = False
    if as_private:
        if user in followed_by:
            while done == False:

                try:
                    tweepy_api.send_direct_message( user, text=msg )
                    done = True
                    result = True
                except tweepy.RateLimitError:
                    print( "Rate limit reached. Waiting 1 min" );
                    time.sleep( 60 )
                    if wait_for_rate == False:
                        done = True
                except:
                    done = True
        else:
            print( "User {} is not following us".format( user ) );
    if as_public:
        if len( user ) > 1:
            msg = user + " " + msg
        msglen = len( urllib.parse.quote_plus( msg ) )
        if msglen >= 139 :
            msg = msg[0:134] + "..."

        while done == False:
            try:
                tweepy_api.update_status( user + " " + msg ) 
                done = True
                result = True
            except tweepy.RateLimitError:
                print( "Rate limit reached. Waiting 1 min" );
                if wait_for_rate:
                    time.sleep( 60 )
                else:
                    done = True
            except tweepy.TweepError as e:
                done = True
                if e.api_code == 187:
                    done = True
                    print( "Message {} is a duplicate!".format( msg ) );
                else:

                    print( "Twitting :{}: len :{}:".format( msg, len(msg) ) );
                    print( "Leaving! Error {} - {}".format( e.api_code, e.reason ) )
                    exit( 1 )
    return result

def generate_timestamp_str_for_file( timestamp_as_str ):
    fnametstamp = "na"
    if check_if_str_valid( timestamp_as_str ):
        YEAR=timestamp_as_str[0:4]
        MONTH=timestamp_as_str[5:7]
        DAY=timestamp_as_str[8:10]
        HOUR=timestamp_as_str[11:13]
        MIN=timestamp_as_str[14:16]
        if int(MONTH) > 12:
            MONTHtmp = DAY
            DAY = MONTH
            MONTH = MONTHtmp
        fnametstamp = "{}{}{}{}{}".format( YEAR, MONTH, DAY, HOUR, MIN )
    return fnametstamp

def generate_timestamp_str_for_dm( timestamp_as_str ):
    fnametstamp = "na"
    if check_if_str_valid( timestamp_as_str ):
        YEAR=timestamp_as_str[0:4]
        MONTH=timestamp_as_str[5:7]
        DAY=timestamp_as_str[8:10]
        HOUR=timestamp_as_str[11:13]
        MIN=timestamp_as_str[14:16]
        if int(MONTH) > 12:
            MONTHtmp = DAY
            DAY = MONTH
            MONTH = MONTHtmp
        fnametstamp = "{}/{}/{}-{}:{}".format( DAY,MONTH,YEAR,HOUR,MIN )
    return fnametstamp

def generate_timestamp( timestamp_as_str ):
    result = "na"
    if check_if_str_valid( timestamp_as_str ):
        YEAR=timestamp_as_str[0:4]
        MONTH=timestamp_as_str[5:7]
        DAY=timestamp_as_str[8:10]
        HOUR=timestamp_as_str[11:13]
        MIN=timestamp_as_str[14:16]
        SEC=timestamp_as_str[17:19]
        if int(MONTH) > 12:
            MONTHtmp = DAY
            DAY = MONTH
            MONTH = MONTHtmp

        time_str="{}/{}/{}-{}:{}:{}".format( DAY,MONTH,YEAR,HOUR,MIN,SEC )
        print( "Found stamp {}".format( time_str ) );
        result = datetime.datetime.strptime( time_str, "%d/%m/%Y-%H:%M:%S"  ).timestamp()

    return result

def read_enckeys( ):
    r_array = []
    with open( "enc_sent.txt", "r" ) as d_file:
        for line in d_file:
            r_array.append( line.rstrip() )
    return r_array

def store_enckeys( d_array ):
    d_file = open( "enc_sent.txt", "w+" )
    d_file.seek(0)
    for it in d_array:
        d_file.write( "%s\n" % it )
    d_file.truncate( )

def check_if_url_exists( url ):
    result = False
    req = http.request( 'HEAD', url )
    if req.status == 200:
        result = True
    return result

def get_twitter_config( ):
    result = False
    req = http.request( 'GET', 'https://api.twitter.com/1.1/help/configuration.json' )
    if req:
        print( "twitter conf {}".format( req.data ) )
        result = True
    return result

generate_last_stamps( )
load_last_ids( )
load_last_stamps()
encoded_sent = read_enckeys( )

app_token=sys.argv[1]
app_secret=sys.argv[2]
access_token=sys.argv[3]
access_secret=sys.argv[4]
# Se hace Auth
#
auth = tweepy.OAuthHandler( app_token, app_secret )
auth.set_access_token(  access_token, access_secret )

# Se obtiene el objeto API
api = tweepy.API( auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True )

# Se compila la lista de seguidores
#populate_my_follower_list()

http = urllib3.PoolManager( )

#Set to TRUE for debugging:
debug_mode = True
debug_mode_pvt = True# False

store_enckeys( encoded_sent )

done = False
while done == False:
    # Se obtiene la lista de noticias.
    NEWSFEEDIMG=""
    NEWSFEED=""
    req = http.request( 'GET', NEWSFEED )
    # Data is now at req.data
    procdatatab = flask.json.loads( req.data )

    #tabs = [ "albergues", "otros"] 
    #tab = "urgencias"
    tab_n = 0

    for tab in tabs:
        procdata = procdatatab[ tab ]
        #print( procdata )
        ENTRY=0
        entries = len(procdata)

        start_tweeting = False

        print( "Trabajando ahora con {}".format( tab ) );
        while ENTRY < entries:
            
            valid_data = False
            cur_enckey = procdata[ ENTRY ][ 'encoded_key' ]

            if cur_enckey in encoded_sent:
                valid_data = False
            else:
                valid_data = True
                encoded_sent.append( cur_enckey )

            if tab.find( "urgencias" ) > -1:
                if not check_if_str_valid( procdata[ ENTRY ][ 'most_important_required' ] ):
                    valid_data = False

            entry_id = procdata[ENTRY]['id']
            #print( "{} is id {}".format( ENTRY, entry_id ) )
            #print( "Data is now of form {}".format( procdata[ ENTRY ]['requeridos'] ) )
            #Get the date from the last entry we processed.

#            if tab.find( "urgencias" ) > -1 :
#                if check_if_str_valid( procdata[ ENTRY ][ 'most_important_required' ] ) :
#                    valid_data = True
#            elif tab.find( "albergues" ) > -1 :
#                if check_if_str_valid( procdata[ ENTRY ][ 'receiving' ] ):
#                    valid_data = True
#            elif tab.find( "otros" ) > -1 :
#                if check_if_str_valid( procdata[ ENTRY ][ 'description' ] ):
#                    valid_data = True
#            elif tab.find( "ofrecimientos" ) > -1 :
#                if check_if_str_valid( procdata[ ENTRY ][ 'offering_details' ] ):
#                    valid_data = True
#            else:
#                if check_if_str_valid( procdata[ ENTRY ][ 'requirements_details' ] ):
#                    valid_data = True
                


            if valid_data:

                start_tweeting = True

                cur_stamp = generate_timestamp( procdata[ ENTRY ][ 'created_at' ] )

                print( "cur {} against last {} ".format( cur_stamp, proc_stamps[ tab_n ] ) )
                #print( "{} against {} ".format( entry_id, proc_ids[ tab_n ] ) )
                    
                #delete me!
#                if start_tweeting:
#                    print( "Now tweeting" );
#                    if( entry_id > proc_ids[ tab_n ] ):
#                        proc_ids[ tab_n ] = entry_id 
#                        print( "Updating ID to {}".format( entry_id ) )
#                    if( cur_stamp > proc_stamps[ tab_n ] ):
#                        proc_stamps[ tab_n ] = cur_stamp
#                        print( "Updating stamp to {}".format( cur_stamp ) )
#                else:
#                    print( "Not tweeting!" )

                if start_tweeting:

                    #Used only for 'urgencias'
                    filename=""

                    if( entry_id > proc_ids[ tab_n ] ):
                        proc_ids[ tab_n ] = entry_id 
                    if( cur_stamp > proc_stamps[ tab_n ] ):
                        proc_stamps[ tab_n ] = cur_stamp
                    
                    msg = ""


                    if tab.find( "centros" ) > -1 or tab.find( "albergues" ) > -1:
                        msg += " " + tab[:-1].upper() + ": "
                        # Poner el mapa al principio
                        if check_if_str_valid( procdata[ ENTRY ][ 'map' ] ):
                            newurl = bitly_my_url( procdata[ ENTRY ][ 'map' ].replace( "\\", "" ) )
                            if newurl.find( "http" ) > -1 :
                                msg += newurl + " "
                    elif tab.find( "otros" ) > -1:
                        if check_if_str_valid( procdata[ ENTRY ][ 'description' ] ):
                            msg += " LINK:"
                            newurl = bitly_my_url( procdata[ ENTRY ][ 'description' ].replace( "\\", "" ) )
                            if newurl.find( "http" ) > -1 :
                                msg += newurl + " "
                        
                        msg += procdata[ ENTRY ]['url']

                    elif tab.find( "urgencias" ) > -1:
                        if procdata[ ENTRY ][ 'urgency_level' ].find( "alto" ) > -1:
                            msg += "URGENTE: "
                        else:
                            msg += "NECESITAMOS: "

                        msg += procdata[ ENTRY ]['most_important_required'].replace( "URGE", "" ).replace( ":", "" )
                        if check_if_str_valid( procdata[ ENTRY ][ 'not_required' ] ):
                            msg += " Abstenerse: " + procdata[ ENTRY ][ 'not_required' ]
                    
                        if check_if_str_valid( procdata[ ENTRY ][ 'source' ] )  :
                            msg += ". FUENTE: " + procdata[ ENTRY ][ 'source' ].replace( "\\", "" ) 

                        if check_if_str_valid( procdata[ ENTRY ][ 'address' ] ):
                            msg += " en " + procdata[ ENTRY ][ 'address' ]
                        if check_if_str_valid( procdata[ ENTRY ][ 'zone' ] ):
                            msg += " Zona " + procdata[ ENTRY ][ 'zone' ]

                    elif tab.find( "ofrecimientos" ) > -1:
                        msg += procdata[ ENTRY ][ 'offering_from' ] 
                        msg += " OFRECE: " 
                        msg += procdata[ ENTRY ][ 'notes' ] 
                        msg += " Contacto: "
                        msg += procdata[ ENTRY ][ 'contact' ] 
                        msg += " Mas informacion: "
                        msg += procdata[ ENTRY ][ 'offering_details' ] 


                    if tab.find( "albergues" ) > -1 :
                        msg += procdata[ ENTRY ]['location']
                        msg += " en " + procdata[ ENTRY ][ 'address' ]
                        msg += " Zona " + procdata[ ENTRY ][ 'zone' ]

                    #else: #
                    if tab.find( "centros" ) > -1 :
                        if check_if_str_valid( procdata[ ENTRY ][ 'map' ] ):
                            if check_if_str_valid( procdata[ ENTRY ][ 'contact' ] ):
                                msg += "Contacto " + procdata[ ENTRY ][ 'contact' ] + " - " 
                            if check_if_str_valid( procdata[ ENTRY ][ 'requirements_details' ] ):
                                msg += procdata[ ENTRY ]['requirements_details']
                            if check_if_str_valid( procdata[ ENTRY ][ 'address' ] ):
                                msg += " en " + procdata[ ENTRY ][ 'address' ]
                            if check_if_str_valid( procdata[ ENTRY ][ 'zone' ] ):
                                msg += " Zona " + procdata[ ENTRY ][ 'zone' ]
                        else:
                            if check_if_str_valid( procdata[ ENTRY ][ 'contact' ] ):
                                msg += "Contacto " + procdata[ ENTRY ][ 'contact' ] + " - "
                            if check_if_str_valid( procdata[ ENTRY ][ 'address' ] ):
                                msg += " " + procdata[ ENTRY ][ 'address' ]
                            if check_if_str_valid( procdata[ ENTRY ][ 'requirements_details' ] ):
                                msg += " " + procdata[ ENTRY ]['requirements_details']
                            if check_if_str_valid( procdata[ ENTRY ][ 'zone' ] ):
                                msg += " Zona " + procdata[ ENTRY ][ 'zone' ]

                        #print( "Cur msg :{}:".format(msg) );
                    #Calcular filename en servidor
                    if tab.find( "urgencias" ) > -1 :
                        fnametstamp = generate_timestamp_str_for_file( procdata[ ENTRY ][ 'updated_at' ] )
                        if fnametstamp.find( "na" ) > -1:
                            filename = ""
                        else:
                            filename = re.sub( " ", "", procdata[ ENTRY ][ 'zone' ].lower() )
                            filename+= "-" + procdata[ ENTRY ][ 'urgency_level' ].lower() + "-" + fnametstamp + ".png"


                    
                    for user in influencers:
                        result = False
                        time_str = generate_timestamp_str_for_dm( procdata[ ENTRY ][ 'created_at' ] )
                        dm_msg = time_str + " " + msg
                        if tab.find( "urgencias" ) > -1 :
                            if len( filename ) > 2:
                                dm_msg += ". http://aquinecesitamos.paw.mx/" + filename #procdata[ ENTRY ][ 'file_name' ]

                        if debug_mode_pvt == False:

                            result = send_private_or_public( api, "@"+user, dm_msg, True, False, False )
                            time.sleep( 5 )
                        else:
                            result = True
                    
                        if result:
                            print( "Enviando dm a {} : '{}'".format( user, msg ) )
                        else:
                            print( "Fallo enviando dm a {} ".format( user, msg ) )
                        
                    
                    if tab.find( "urgencias" ) > -1 :
                        # Shorten the tweet right here,
                        cur_tweet_len = len( msg )
                        cur_source_len = 0
                        http_starts = 0
                        if check_if_str_valid( procdata[ ENTRY ][ 'source' ] ):
                            cur_source = procdata[ ENTRY ][ 'source' ]
                            cur_source_len = len( cur_source )
                            http_starts = cur_source.find( "http" )
                            cur_source_len -= http_starts
                        #is it a link
                        if msg.find( "http" ) > -1:
                            if cur_source_len > 23:
                                cur_tweet_len -= cur_source_len
                                cur_tweet_len += 23

                        #print( "Msg {} is {} len {} link len {} starts {}".format( msg, cur_source, cur_source_len, len(msg), http_starts ) )
                        if cur_tweet_len >= 140:
                            msg = msg[0:138]

                        imgurl = "http://aquinecesitamos.paw.mx/" +  urllib.parse.quote_plus( filename )
                        #print( "Imgurl: {}".format( imgurl ) )
                        if not check_if_url_exists( imgurl ):
                            filename = ""
                        if len( filename ) > 2:

                            #print( "Mandando imagen {}".format( imgurl) );
                                                               # No recortar el tweet!
                            if debug_mode == False:
                                result = send_image( api, imgurl, msg, False, True )
                            else:
                                result = True

                        else:
                            if debug_mode == False:
                                result = send_private_or_public( api, "", msg, False, True, True )
                            else:
                                result = True
                                print( "DEB: Enviando public {} - fecha creacion {}, update {}".format( msg, procdata[ ENTRY ]['created_at'], procdata[ ENTRY ]['updated_at'] ) )
                    else:
                        if debug_mode == False:
                            result = send_private_or_public( api, "", msg, False, True, True )
                        else:
                            result = True
                            print( "DEB: Enviando public {}".format( msg ) )

                    if result:
                        print( "Enviando public " )
                    else:
                        print( "Fallo enviando public {}".format( msg ) )
                    time.sleep( 30 )

                
                else:
                    print( "Already processed ID!" );

        
            ENTRY += 1
            
            store_enckeys( encoded_sent )
            if valid_data:
                time.sleep( 10 )
            #ENTRY -= 1

        tab_n += 1
        store_last_ids()
        store_last_stamps( )

    #time.sleep( 60 * 2 )
    populate_my_follower_list()



exit(1)


