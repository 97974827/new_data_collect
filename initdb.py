import gls_config
import pymysql

conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
curs = conn.cursor(pymysql.cursors.DictCursor)


try:
    with conn.cursor():
        try:
            print("reset gl_air_config...")
            acd = "DELETE FROM gl_air_config"
            acr = "ALTER TABLE gl_air_config auto_increment = 1 "
            curs.execute(acd)
            conn.commit()
            curs.execute(acr)
            conn.commit()
        except Exception as e:
            print("From reset_gl_air_config except :", e)
        finally:
            print("completed ! ")


        try:
            print("reset gl_air_state...")
            asd = "DELETE FROM gl_air_state"
            asr = "ALTER TABLE gl_air_state auto_increment = 1 "
            curs.execute(asd)
            conn.commit()
            curs.execute(asr)
            conn.commit()
        except Exception as e:
            print("From reset_gl_air_state except : ", e)
        finally:
            print("completed ! ")


        try:
            print("Drop gl_back_ip...")
            dbi = "DROP TABLE gl_back_ip"
            curs.execute(dbi)
            conn.commit()
        except Exception as e:
            print("From Drop gl_back_ip...")
        finally:
            print("completed ! ")


        try:
            print("reset gl_card...")
            cd = "DELETE FROM gl_card"
            cr = "ALTER TABLE gl_card auto_increment = 1 "
            ci = "INSERT INTO gl_card(`card_num`) VALUES('00000000')"
            curs.execute(cd)
            conn.commit()
            curs.execute(cr)
            conn.commit()
            curs.execute(ci)
            conn.commit()
        except Exception as e:
            print("From reset gl_card except : ", e)
        finally:
            print("completed !")


        try:
            print("reset gl_card_blacklist...")
            cbd = "DELETE FROM gl_card_blacklist"
            cbr = "ALTER TABLE gl_card_blacklist auto_increment = 1 "
            curs.execute(cbd)
            conn.commit()
            curs.execute(cbr)
            conn.commit()
        except Exception as e:
            print("From reset gl_card_blacklist except : ", e)
        finally:
            print("completed !")

        try:
            print("reset gl_charger_config...")
            ccd = "DELETE FROM gl_charger_config"
            ccr = "ALTER TABLE gl_charger_config auto_increment = 1 "
            curs.execute(ccd)
            conn.commit()
            curs.execute(ccr)
            conn.commit()
        except Exception as e:
            print("From reset gl_charger_config except : ", e)
        finally:
            print("completed !")

        try:
            print("reset gl_charger_state...")
            csd = "DELETE FROM gl_charger_state"
            csr = "ALTER TABLE gl_charger_state auto_increment = 1 "
            curs.execute(csd)
            conn.commit()
            curs.execute(csr)
            conn.commit()
        except Exception as e:
            print("From reset gl_charger_state except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_charger_state...")
            csd = "DELETE FROM gl_charger_state"
            csr = "ALTER TABLE gl_charger_state auto_increment = 1 "
            curs.execute(csd)
            conn.commit()
            curs.execute(csr)
            conn.commit()
        except Exception as e:
            print("From reset gl_charger_state except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_credit_card_config...")
            cccd = "DELETE FROM gl_credit_card_config"
            cccr = "ALTER TABLE gl_credit_card_config auto_increment = 1 "
            curs.execute(cccd)
            conn.commit()
            curs.execute(cccr)
            conn.commit()
        except Exception as e:
            print("From reset gl_credit_card_config except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_credit_card_log...")
            ccld = "DELETE FROM gl_credit_card_log"
            cclr = "ALTER TABLE gl_credit_card_log auto_increment = 1 "
            curs.execute(ccld)
            conn.commit()
            curs.execute(cclr)
            conn.commit()
        except Exception as e:
            print("From reset gl_credit_card_log except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_device_list...")
            dld = "DELETE FROM gl_device_list"
            dlr = "ALTER TABLE gl_device_list auto_increment = 1 "
            dli = "INSERT INTO gl_device_list(`type`, `addr`) VALUES (%s, %s)"
            curs.execute(dld)
            conn.commit()
            curs.execute(dlr)
            conn.commit()
            curs.execute(dli, ('8', '01'))
            conn.commit()
        except Exception as e:
            print("From reset gl_device_list except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_err_log...")
            eld = "DELETE FROM gl_err_log"
            elr = "ALTER TABLE gl_err_log auto_increment = 1 "
            curs.execute(eld)
            conn.commit()
            curs.execute(elr)
            conn.commit()
        except Exception as e:
            print("From reset gl_err_log except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_garage_config...")
            gcd = "DELETE FROM gl_garage_config"
            gcr = "ALTER TABLE gl_garage_config auto_increment = 1 "
            curs.execute(gcd)
            conn.commit()
            curs.execute(gcr)
            conn.commit()
        except Exception as e:
            print("From reset gl_garage_config except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_garage_state...")
            gsd = "DELETE FROM gl_garage_state"
            gsr = "ALTER TABLE gl_garage_state auto_increment = 1 "
            curs.execute(gsd)
            conn.commit()
            curs.execute(gsr)
            conn.commit()
        except Exception as e:
            print("From reset gl_garage_state except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_mate_config...")
            mcd = "DELETE FROM gl_mate_config"
            mcr = "ALTER TABLE gl_mate_config auto_increment = 1 "
            curs.execute(mcd)
            conn.commit()
            curs.execute(mcr)
            conn.commit()
        except Exception as e:
            print("From reset gl_mate_config except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_mate_state...")
            msd = "DELETE FROM gl_mate_state"
            msr = "ALTER TABLE gl_mate_state auto_increment = 1 "
            curs.execute(msd)
            conn.commit()
            curs.execute(msr)
            conn.commit()
        except Exception as e:
            print("From reset gl_mate_state except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_member...")
            md = "DELETE FROM gl_member"
            mr = "ALTER TABLE gl_member auto_increment = 1 "
            curs.execute(md)
            conn.commit()
            curs.execute(mr)
            conn.commit()
        except Exception as e:
            print("From reset gl_member except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_member_card...")
            mccd = "DELETE FROM gl_member_card"
            mccr = "ALTER TABLE gl_member_card auto_increment = 1 "
            curs.execute(mccd)
            conn.commit()
            curs.execute(mccr)
            conn.commit()
        except Exception as e:
            print("From reset gl_member_card except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_self_config...")
            scd = "DELETE FROM gl_self_config"
            scr = "ALTER TABLE gl_self_config auto_increment = 1 "
            curs.execute(scd)
            conn.commit()
            curs.execute(scr)
            conn.commit()
        except Exception as e:
            print("From reset gl_self_config except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_self_state...")
            ssd = "DELETE FROM gl_self_state"
            ssr = "ALTER TABLE gl_self_state auto_increment = 1 "
            curs.execute(ssd)
            conn.commit()
            curs.execute(ssr)
            conn.commit()
        except Exception as e:
            print("From reset gl_self_state except : ", e)
        finally:
            print("complected")

        try:
            print("reset gl_wash_total...")
            wtd = "DELETE FROM gl_wash_total"
            wtr = "ALTER TABLE gl_wash_total auto_increment = 1 "
            curs.execute(wtd)
            conn.commit()
            curs.execute(wtr)
            conn.commit()
        except Exception as e:
            print("From reset gl_wash_total except : ", e)
        finally:
            print("complected")
finally:
    conn.close()