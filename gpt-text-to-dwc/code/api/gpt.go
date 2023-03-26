package gpt

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"errors"
	"log"
)

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

func ExtractDWC(ocrText string) (map[string]interface{}, error) {
	url := "https://api.openai.com/v1/chat/completions"
	systemPrompt := `I accurately classify extracted OCR text from herbarium specimen scans into only the following Darwin Core terms:

	- scientificName: Full scientific name, not containing identification qualifications.
	- catalogNumber: Unique identifier for the record in the dataset or collection.
	- recordNumber: Identifier given during recording, often linking field notes and Occurrence record.
	- recordedBy: List of people, groups, or organizations responsible for recording the original Occurrence.
	- year: Four-digit year of the Event.
	- month: Integer for the month of the Event.
	- day: Integer for the day of the Event.
	- dateIdentified: Date when the subject was determined to represent the Taxon.
	- identifiedBy: Person, group, or organization assigning the Taxon to the subject.
	- verbatimIdentification: Taxonomic identification as it appeared in the original record.
	- kingdom: Full scientific name of the kingdom in which the taxon is classified.
	- country: Name of the country or major administrative unit for the Location.
	- countryCode: Standard code for the country of the Location.
	- decimalLatitude: Geographic latitude in decimal degrees of the Location's center.
	- decimalLongitude: Geographic longitude in decimal degrees of the Location's center.
	- location: A spatial region or named place.
	- minimumElevationInMeters: The lower limit of the range of elevation in meters.
	- maximumElevationInMeters: The upper limit of the range of elevation in meters.
	- verbatimElevation: The original description of the elevation.

	"|" separates multiple strings in one term. If I can't identify information for a specific term, I don't include it.
	My responses are minified JSON.`

	log.Printf("Extracting DWC from: %s", ocrText)

	if ocrText == "" {
		return nil, errors.New("No text provided")
	}

	messages := []Message{
		{
			Role:    "system",
			Content: systemPrompt,
		},
		{
			Role:    "user",
			Content: ocrText,
		},
	}

	data := map[string]interface{}{
		"model":    os.Getenv("GPT_MODEL"),
		"messages": messages,
	}

	dataBytes, err := json.Marshal(data)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(dataBytes))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", os.Getenv("GPT_API_KEY")))

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var jsonResponse map[string]interface{}
	err = json.Unmarshal(body, &jsonResponse)
	if err != nil {
		return nil, err
	}

	log.Printf("Finished extracting DWC. Result: %s", jsonResponse)
	
	return jsonResponse, nil
}
