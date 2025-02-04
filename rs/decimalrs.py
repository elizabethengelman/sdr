#!/usr/bin/env python3

class DecimalRS:
	NO_ERRORS = 0
	DIGIT = 1
	CORRECTED = 2
	DIGIT_PROBABLY = 3
	UNCORRECTABLE = 4

	def __init__(self, k, weakened):
		# Size of the original message
		self.k = k
		if self.k > 7 or self.k < 1:
			raise Exception("k must be 1..7")
		# Final size of the encoded message
		self.n = k + 3
		# Size of the redundancy code
		self.nmk = self.n - self.k
		# Convert 'X' digits to zero
		self.weakened = weakened

	def calc_rs_digit(self, msg, d):
		# Message polynomial is evaluated with a different x
		# for every RS digit. We use the n-th power of a field
		# generator (2).
		x = 2 ** d % 11
		tot = 0
		for b in range(1, len(msg) + 1):
			a = int("0" + msg[-b], 10)
			tot += (a * x ** b) % 11
		tot = tot % 11
		if tot == 10:
			if self.weakened:
				tot = 0
			else:
				return "X"
		return "%01d" % tot

	def _encode(self, msg):
		rs_digits = ""
		for rs_digit in range(1, self.nmk + 1):
			rs_digits += self.calc_rs_digit(msg, rs_digit)
		return rs_digits

	def encode(self, msg):
		if msg < 0:
			raise Exception("msg must be a non-negative number")

		msg = "%d" % msg
		if len(msg) < self.k:
			msg = ("0" * (self.k - len(msg))) + msg
		if len(msg) > self.k:
			raise Exception("msg is too big to fit in this code")

		# Append redundancy code
		msg = msg + self._encode(msg)

		# May have 'X' digits, so must be returned as string
		return msg

	def different_digits(self, d):
		a = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
		a.remove(d)
		assert(len(a) == 9)
		return a

	def find_syndromes(self, rs1, rs2):
		syndromes = {}
		for i in range(1, len(rs1) + 1):
			if rs1[-i] == rs2[-i]:
				continue
			y = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "X"].index(rs2[-i].upper())
			x = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "X"].index(rs1[-i].upper())
			syndromes[i] = (y - x) % 11
				
		return syndromes

	def decode(self, msg):
		if isinstance(msg, int):
			msg = "%d" % msg
		msg = msg.strip()
		if len(msg) < self.n:
			msg = ("0" * (self.n - len(msg))) + msg
		elif len(msg) > self.n:
			raise Exception("encoded msg must be a string with length === n")

		base_msg = msg[0:self.k]
		got_rs = msg[self.k:]

		calc_rs = self._encode(base_msg)
		syndromes = self.find_syndromes(got_rs, calc_rs)

		if len(syndromes) == 0:
			return int(base_msg), DecimalRS.NO_ERRORS

		# If there is a single diff in RS code, the single error is 
		# in the RS code itself. But, when the code is weakened, this
		# is not 100% guaranteed.

		if len(syndromes) == 1:
			if not self.weakened:
				return int(base_msg), DecimalRS.DIGIT
			else:
				return int(base_msg), DecimalRS.DIGIT_PROBABLY

		# We can only correct one error, so it is feasible to try all
		# combinations to see if anyone matches the received RS code

		for i in range(0, self.k):
			for p in self.different_digits(base_msg[i]):
				test_msg = base_msg[0:i] + p + base_msg[i+1:]
				test_rs = self._encode(test_msg)
				if test_rs == got_rs:
					# Found a good one (probably!)
					return int(test_msg), DecimalRS.CORRECTED

		# A single diff in weakened code probably means the message
		# is good, ***BUT*** it is not 100% certain. The API client
		# must decide what to do in this case.

		return None, DecimalRS.UNCORRECTABLE
		

if __name__ == "__main__":
	rs = DecimalRS(7, False)
	rsw = DecimalRS(7, True)
	e = rs.encode(3141592)
	assert (e == "3141592134")
	e = rsw.encode(3141592)
	assert (e == "3141592134")
	e = rs.encode(3141591)
	assert (e == "3141591XX7")
	e = rsw.encode(3141591)
	assert (e == "3141591007")
	# No errors
	assert (rs.decode(3141592134) == (3141592, DecimalRS.NO_ERRORS))
	assert (rsw.decode(3141592134) == (3141592, DecimalRS.NO_ERRORS))
	assert (rs.decode("3141591XX7") == (3141591, DecimalRS.NO_ERRORS))
	assert (rsw.decode("3141591007") == (3141591, DecimalRS.NO_ERRORS))
	# Single error in RS code itself
	assert (rs.decode(3141592133) == (3141592, DecimalRS.DIGIT))
	assert (rsw.decode(3141592133) == (3141592, DecimalRS.DIGIT_PROBABLY))
	# Single error in main msg
	assert (rs.decode(3142592134) == (3141592, DecimalRS.CORRECTED))
	assert (rsw.decode(3142592134) == (3141592, DecimalRS.CORRECTED))
	# Two errors in main msg
	assert (rs.decode(9142592134) == (None, DecimalRS.UNCORRECTABLE))
	assert (rsw.decode(9142592134) == (None, DecimalRS.UNCORRECTABLE))
	# Two errors in RS code itself
	assert (rs.decode(3141592335) == (None, DecimalRS.UNCORRECTABLE))

	print("Ok")
