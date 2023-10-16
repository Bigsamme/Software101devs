class Solution(object):
    def isValid(self, s):
        ma = {
            "(":")",
            "[":"]",
            "{":"}",
            "]":"[",
            ")":""       
        }
        skip = False

        for char in range(int(len(s)/2)):
            if skip:
                skip = False
            
            else:
                if ma[s[int(len(s)/2- char ) ]] == s[int(len(s)/2 + char)]:
                    skip = True
                else: return False
        return True


sol = Solution()

print(sol.isValid("(]"))