package annotate

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"io/ioutil"
	"os"
	"log"
)

func Annotate(ID *string, text *string, source string, notes string) (map[string]interface{}, error) {
	var url = os.Getenv("ANNOTATER_URI")
	log.Printf("Starting annotation process for: %s", text)

	headers := map[string]string{
		"Authorization": fmt.Sprintf("Token %s", os.Getenv("ANNOTATER_KEY")),
	}

	var annotation interface{}
	if err := json.Unmarshal([]byte(*text), &annotation); err != nil {
		// If the text couldn't be parsed as JSON, use it as a string
		annotation = *text
	}

	data := map[string]interface{}{
		"resolvable_object_id": ID,
		"annotation":           annotation,
		"source":               source,
		"notes":                notes,
	}

	jsonData, err := json.Marshal(data)
	if err != nil {
		log.Printf("Error in marshalling JSON data:", err)
		return nil, nil
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("Error in creating a new request:", err)
		return nil, nil
	}

	for key, value := range headers {
		req.Header.Set(key, value)
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Error in sending request:", err)
		return nil, err
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Error in reading request:", err)
		return nil, err
	}

	var jsonResponse map[string]interface{}
	err = json.Unmarshal(body, &jsonResponse)
	if err != nil {
		return nil, err
	}

	log.Printf("Finished annotation process")
	return jsonResponse, nil
}
