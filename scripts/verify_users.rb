include Process

def prepare_users(range_group)
  thread_count = 8
  thread_pool = Concurrent::FixedThreadPool.new(thread_count)

  range_group.each do |range|
    range.each do |usernum| 
      Rails.application.executor.wrap do
        thread_pool.post do
          prepare_user(usernum)
        end
      end
    end
    puts "Users #{range.first} - #{range.last} prepared"
  end

  thread_pool.shutdown
  thread_pool.wait_for_termination
end

def prepare_user(usernum)
  # check if email exists, then if the user attached exists
  email = "testuser#{usernum}@example.com"
  user = User.find_with_email(email)
    if user
      user = validate_phone(user)
      user.accepted_terms_at = DateTime.now 
      user.second_factor_locked_at = nil
      user.second_factor_attempts_count = 0
      user.save
    else
      warn "User`#{email}` doesn't exist"
      generate_user(usernum)
    end
end

def validate_phone(user)
  if user.phone_configurations.first == nil
    MfaContext.new(user).phone_configurations.create(phone_configuration_data(user))
  else
    phone_config = user.phone_configurations.first
    if Phonelib.valid_for_country?(phone_config.phone, 'US')
      return user
    else
      phone_config.phone = PhoneFormatter.format(valid_phone)
      phone_config.save
    end
  end
  return user
end

def generate_user(usernum)
  email_addr = "testuser#{usernum}@example.com"
  puts "Creating user #{email_addr}"
  ee = EncryptedAttribute.new_from_decrypted(email_addr)
  pw = 'salty pickles'
  User.create! do |user|
    setup_user(user, ee: ee, pw: pw, num: usernum)
  end
end

def setup_user(user, args)
  EmailAddress.create!(user: user, email: args[:ee].decrypted, confirmed_at: Time.zone.now)
  user.reset_password(args[:pw], args[:pw])
  MfaContext.new(user).phone_configurations.create(phone_configuration_data(user))
  user.email_addresses.update_all(confirmed_at: Time.zone.now)
  user.accepted_terms_at = DateTime.now
  user.save
end

# https://github.com/faker-ruby/faker/blob/master/lib/locales/en-US.yml#L92
AREA_CODES = ["201", "202", "203", "205", "206", "207", "208", "209", "210", "212", "213", "214", "215", "216", "217", "218", "219", "224", "225", "228", "229", "231", "234", "239", "240", "248", "251", "252", "253", "254", "256", "260", "262", "267", "269", "270", "276", "281", "301", "302", "303", "304", "305", "307", "308", "309", "310", "312", "313", "314", "315", "316", "317", "318", "319", "320", "321", "323", "330", "334", "336", "337", "339", "347", "351", "352", "360", "361", "386", "401", "402", "404", "405", "406", "407", "408", "409", "410", "412", "413", "414", "415", "417", "419", "423", "424", "425", "434", "435", "440", "443", "469", "478", "479", "480", "484", "501", "502", "503", "504", "505", "507", "508", "509", "510", "512", "513", "515", "516", "517", "518", "520", "530", "540", "541", "551", "559", "561", "562", "563", "567", "570", "571", "573", "574", "580", "585", "586", "601", "602", "603", "605", "606", "607", "608", "609", "610", "612", "614", "615", "616", "617", "618", "619", "620", "623", "626", "630", "631", "636", "641", "646", "650", "651", "660", "661", "662", "678", "682", "701", "702", "703", "704", "706", "707", "708", "712", "713", "714", "715", "716", "717", "718", "719", "720", "724", "727", "731", "732", "734", "740", "754", "757", "760", "763", "765", "770", "772", "773", "774", "775", "781", "785", "786", "801", "802", "803", "804", "805", "806", "808", "810", "812", "813", "814", "815", "816", "817", "818", "828", "830", "831", "832", "843", "845", "847", "848", "850", "856", "857", "858", "859", "860", "862", "863", "864", "865", "870", "878", "901", "903", "904", "906", "907", "908", "909", "910", "912", "913", "914", "915", "916", "917", "918", "919", "920", "925", "928", "931", "936", "937", "940", "941", "947", "949", "952", "954", "956", "970", "971", "972", "973", "978", "979", "980", "985", "989"]
EXCHANGE_CODES = ["201", "202", "203", "205", "206", "207", "208", "209", "210", "212", "213", "214", "215", "216", "217", "218", "219", "224", "225", "227", "228", "229", "231", "234", "239", "240", "248", "251", "252", "253", "254", "256", "260", "262", "267", "269", "270", "276", "281", "283", "301", "302", "303", "304", "305", "307", "308", "309", "310", "312", "313", "314", "315", "316", "317", "318", "319", "320", "321", "323", "330", "331", "334", "336", "337", "339", "347", "351", "352", "360", "361", "386", "401", "402", "404", "405", "406", "407", "408", "409", "410", "412", "413", "414", "415", "417", "419", "423", "424", "425", "434", "435", "440", "443", "445", "464", "469", "470", "475", "478", "479", "480", "484", "501", "502", "503", "504", "505", "507", "508", "509", "510", "512", "513", "515", "516", "517", "518", "520", "530", "540", "541", "551", "557", "559", "561", "562", "563", "564", "567", "570", "571", "573", "574", "580", "585", "586", "601", "602", "603", "605", "606", "607", "608", "609", "610", "612", "614", "615", "616", "617", "618", "619", "620", "623", "626", "630", "631", "636", "641", "646", "650", "651", "660", "661", "662", "667", "678", "682", "701", "702", "703", "704", "706", "707", "708", "712", "713", "714", "715", "716", "717", "718", "719", "720", "724", "727", "731", "732", "734", "737", "740", "754", "757", "760", "763", "765", "770", "772", "773", "774", "775", "781", "785", "786", "801", "802", "803", "804", "805", "806", "808", "810", "812", "813", "814", "815", "816", "817", "818", "828", "830", "831", "832", "835", "843", "845", "847", "848", "850", "856", "857", "858", "859", "860", "862", "863", "864", "865", "870", "872", "878", "901", "903", "904", "906", "907", "908", "909", "910", "912", "913", "914", "915", "916", "917", "918", "919", "920", "925", "928", "931", "936", "937", "940", "941", "947", "949", "952", "954", "956", "959", "970", "971", "972", "973", "975", "978", "979", "980", "984", "985", "989"]

def random_us_phone
  "#{AREA_CODES.sample}-#{EXCHANGE_CODES.sample}-#{format("%4d", rand(9999))}"
end

def valid_phone
  validity = false
  while validity == false
    phone = random_us_phone
    # is this the same as the rails app?
    validity = Phonelib.valid_for_country?(phone, 'US')
  end
  phone
end

def phone_configuration_data(user)
  {
    delivery_preference: user.otp_delivery_preference,
    phone: PhoneFormatter.format(random_us_phone),
    confirmed_at: Time.zone.now,
  }
end

def array_of_ranges(start, length, count)
  ranges = []
  count.times do |i|
    if i < 1
      range = start..(start + length)
      ranges << range
    else
      new_start = start + (length * i) + 1
      finish =  start + (length * i) + length
      range = new_start..finish
      ranges << range
    end
  end
  ranges
end

def main(ranges)
  Benchmark.measure {
    # chunk `ranges` to avoid out of memory warnings when 
    # array_of_ranges count is higher than available processors
    ranges.each_slice(Concurrent.processor_count) do |range|
      fork { prepare_users(range) }
    end
    Process.waitall
  }
end

# change range for start, number_of_users_per_range, array_size 
ranges = array_of_ranges(0, 1000, 1000)
results = main(ranges)
results.real